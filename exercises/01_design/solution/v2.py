"""
V2 router, outside-in, consumer-facing.

Exercise 1 solution: raw SQL implementations.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from checkup_api.database import get_db

router = APIRouter(prefix="/v2", tags=["v2"])


def _compute_status(value, higher_is_better, warn, critical) -> str:
    if value is None or warn is None or critical is None:
        return "unknown"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "unknown"
    warn = float(warn)
    critical = float(critical)
    if higher_is_better:
        if v >= warn:
            return "healthy"
        if v >= critical:
            return "warn"
        return "critical"
    else:
        if v <= warn:
            return "healthy"
        if v <= critical:
            return "warn"
        return "critical"


def _latest_with_thresholds(db: Session, slug_filter: str | None = None) -> list[dict]:
    """Latest measurement per (product, metric), joined with metric thresholds."""
    sql = """
        SELECT
            m.tag_product   AS slug,
            m.name          AS metric_name,
            m.value         AS value,
            m.unit          AS unit,
            m.measured_at   AS measured_at,
            m.diagnostic    AS diagnostic,
            mt.category           AS category,
            mt.higher_is_better   AS higher_is_better,
            mt.threshold_warn     AS threshold_warn,
            mt.threshold_critical AS threshold_critical
        FROM measurements m
        JOIN metrics mt ON mt.name = m.name
        JOIN (
            SELECT name, tag_product, MAX(measured_at) AS latest
            FROM measurements
            GROUP BY name, tag_product
        ) latest
          ON latest.name = m.name
         AND latest.tag_product = m.tag_product
         AND latest.latest = m.measured_at
    """
    params: dict = {}
    if slug_filter:
        sql += " WHERE m.tag_product = :slug"
        params["slug"] = slug_filter
    return [dict(r) for r in db.execute(text(sql), params).mappings()]


def _rollup(rows: list[dict]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        bucket = out.setdefault(r["slug"], {"healthy": 0, "warn": 0, "critical": 0})
        s = _compute_status(r["value"], r["higher_is_better"], r["threshold_warn"], r["threshold_critical"])
        if s in bucket:
            bucket[s] += 1
    return out


@router.get("/products")
def list_products(
    db: Annotated[Session, Depends(get_db)],
    entity: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    sort: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """
    List products.
    """

    sql = """
        SELECT p.slug, p.name, p.owner_email, e.name AS entity_name
        FROM products p
        JOIN entities e ON e.id = p.entity_id
    """
    params: dict = {}
    if entity:
        sql += " WHERE e.slug = :entity"
        params["entity"] = entity
    sql += " ORDER BY p.name"
    products = [dict(r) for r in db.execute(text(sql), params).mappings()]

    rollup = _rollup(_latest_with_thresholds(db))

    items = []
    for p in products:
        health = rollup.get(p["slug"], {"healthy": 0, "warn": 0, "critical": 0})
        if status_filter and health.get(status_filter, 0) == 0:
            continue
        items.append({
            "slug": p["slug"],
            "name": p["name"],
            "entity": p["entity_name"],
            "owner_email": p["owner_email"],
            "health": health,
        })

    if sort == "health":
        items.sort(key=lambda x: (x["health"]["critical"], x["health"]["warn"]), reverse=True)

    return items[offset : offset + limit]


@router.get("/products/{slug}")
def get_product(slug: str, db: Annotated[Session, Depends(get_db)]):
    """
    Return product detail.
    """

    row = db.execute(
        text("""
            SELECT p.slug, p.name, p.owner_email, p.created_at, e.name AS entity_name
            FROM products p
            JOIN entities e ON e.id = p.entity_id
            WHERE p.slug = :slug
        """),
        {"slug": slug},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Product {slug!r} not found")

    rollup = _rollup(_latest_with_thresholds(db, slug_filter=slug))
    return {
        "slug": row["slug"],
        "name": row["name"],
        "entity": row["entity_name"],
        "owner_email": row["owner_email"],
        "created_at": row["created_at"],
        "health": rollup.get(slug, {"healthy": 0, "warn": 0, "critical": 0}),
    }


@router.get("/products/{slug}/metrics")
def list_product_metrics(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    category: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
):
    """
    Return the product's most recent measurement per metric, each
    enriched with a derived `status` (healthy/warn/critical).
    """

    if not db.execute(text("SELECT 1 FROM products WHERE slug = :slug"), {"slug": slug}).first():
        raise HTTPException(status_code=404, detail=f"Product {slug!r} not found")

    rows = _latest_with_thresholds(db, slug_filter=slug)

    items = []
    for r in rows:
        if category and r["category"] != category:
            continue
        s = _compute_status(r["value"], r["higher_is_better"], r["threshold_warn"], r["threshold_critical"])
        if status_filter and s != status_filter:
            continue
        items.append({
            "name": r["metric_name"],
            "category": r["category"],
            "value": r["value"],
            "unit": r["unit"],
            "status": s,
            "measured_at": r["measured_at"],
            "diagnostic": r["diagnostic"],
        })
    return items


@router.get("/products/{slug}/metrics/{name}/history")
def get_metric_history(
    slug: str,
    name: str,
    db: Annotated[Session, Depends(get_db)],
    since: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """
    Time series of measurements for a single metric on a single product, most recent first.
    """

    if not db.execute(text("SELECT 1 FROM products WHERE slug = :slug"), {"slug": slug}).first():
        raise HTTPException(status_code=404, detail=f"Product {slug!r} not found")

    sql = """
        SELECT m.value, m.measured_at,
               mt.higher_is_better, mt.threshold_warn, mt.threshold_critical
        FROM measurements m
        JOIN metrics mt ON mt.name = m.name
        WHERE m.tag_product = :slug AND m.name = :name
    """
    params: dict = {"slug": slug, "name": name}
    if since is not None:
        sql += " AND m.measured_at >= :since"
        params["since"] = since
    sql += " ORDER BY m.measured_at DESC LIMIT :limit"
    params["limit"] = limit

    rows = db.execute(text(sql), params).mappings().all()
    return [
        {
            "value": r["value"],
            "measured_at": r["measured_at"],
            "status": _compute_status(r["value"], r["higher_is_better"], r["threshold_warn"], r["threshold_critical"]),
        }
        for r in rows
    ]


@router.get("/metrics")
def list_metrics(
    db: Annotated[Session, Depends(get_db)],
    category: Annotated[str | None, Query()] = None,
):
    """List the metric catalog."""

    sql = """
        SELECT name, category, description, higher_is_better,
               threshold_warn, threshold_critical
        FROM metrics
    """
    params: dict = {}
    if category:
        sql += " WHERE category = :category"
        params["category"] = category
    return [dict(r) for r in db.execute(text(sql), params).mappings()]


@router.get("/metrics/{name}")
def get_metric(name: str, db: Annotated[Session, Depends(get_db)]):
    """
    Return a single metric definition.
    """

    row = db.execute(
        text("""
            SELECT name, category, description, higher_is_better,
                   threshold_warn, threshold_critical
            FROM metrics
            WHERE name = :name
        """),
        {"name": name},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Metric {name!r} not found")
    return dict(row)
