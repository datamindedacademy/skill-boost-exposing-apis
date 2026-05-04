"""
V2 router, outside-in, consumer-facing.

Exercise 2 solution: SQLAlchemy ORM with selectinload to avoid N+1.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from checkup_api.database import get_db
from checkup_api.models import Entity, Measurement, Metric, Product

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


def _latest_per_metric(measurements: list[Measurement]) -> list[Measurement]:
    latest: dict[str, Measurement] = {}
    for m in measurements:
        existing = latest.get(m.name)
        if existing is None or m.measured_at > existing.measured_at:
            latest[m.name] = m
    return list(latest.values())


def _rollup_for_product(p: Product) -> dict[str, int]:
    rollup = {"healthy": 0, "warn": 0, "critical": 0}
    for m in _latest_per_metric(list(p.measurements)):
        s = _compute_status(m.value, m.metric.higher_is_better, m.metric.threshold_warn, m.metric.threshold_critical)
        if s in rollup:
            rollup[s] += 1
    return rollup


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

    stmt = (
        select(Product)
        .join(Entity, Product.entity_id == Entity.id)
        .options(
            contains_eager(Product.entity),
            selectinload(Product.measurements).selectinload(Measurement.metric),
        )
        .order_by(Product.name)
    )
    if entity:
        stmt = stmt.where(Entity.slug == entity)

    products = db.execute(stmt).unique().scalars().all()

    items = []
    for p in products:
        health = _rollup_for_product(p)
        if status_filter and health.get(status_filter, 0) == 0:
            continue
        items.append({
            "slug": p.slug,
            "name": p.name,
            "entity": p.entity.name,
            "owner_email": p.owner_email,
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

    stmt = (
        select(Product)
        .options(
            joinedload(Product.entity),
            selectinload(Product.measurements).selectinload(Measurement.metric),
        )
        .where(Product.slug == slug)
    )
    p = db.execute(stmt).unique().scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail=f"Product {slug!r} not found")

    return {
        "slug": p.slug,
        "name": p.name,
        "entity": p.entity.name,
        "owner_email": p.owner_email,
        "created_at": p.created_at,
        "health": _rollup_for_product(p),
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

    stmt = (
        select(Product)
        .options(selectinload(Product.measurements).selectinload(Measurement.metric))
        .where(Product.slug == slug)
    )
    p = db.execute(stmt).unique().scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail=f"Product {slug!r} not found")

    items = []
    for m in _latest_per_metric(list(p.measurements)):
        if category and m.metric.category != category:
            continue
        s = _compute_status(m.value, m.metric.higher_is_better, m.metric.threshold_warn, m.metric.threshold_critical)
        if status_filter and s != status_filter:
            continue
        items.append({
            "name": m.name,
            "category": m.metric.category,
            "value": m.value,
            "unit": m.unit,
            "status": s,
            "measured_at": m.measured_at,
            "diagnostic": m.diagnostic,
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

    if not db.execute(select(Product.id).where(Product.slug == slug)).first():
        raise HTTPException(status_code=404, detail=f"Product {slug!r} not found")

    stmt = (
        select(Measurement)
        .options(joinedload(Measurement.metric))
        .where(Measurement.tag_product == slug, Measurement.name == name)
        .order_by(Measurement.measured_at.desc())
        .limit(limit)
    )
    if since is not None:
        stmt = stmt.where(Measurement.measured_at >= since)

    measurements = db.execute(stmt).unique().scalars().all()
    return [
        {
            "value": m.value,
            "measured_at": m.measured_at,
            "status": _compute_status(m.value, m.metric.higher_is_better, m.metric.threshold_warn, m.metric.threshold_critical),
        }
        for m in measurements
    ]


@router.get("/metrics")
def list_metrics(
    db: Annotated[Session, Depends(get_db)],
    category: Annotated[str | None, Query()] = None,
):
    """List the metric catalog."""

    stmt = select(Metric)
    if category:
        stmt = stmt.where(Metric.category == category)
    metrics = db.execute(stmt).scalars().all()
    return [
        {
            "name": m.name,
            "category": m.category,
            "description": m.description,
            "higher_is_better": m.higher_is_better,
            "threshold_warn": m.threshold_warn,
            "threshold_critical": m.threshold_critical,
        }
        for m in metrics
    ]


@router.get("/metrics/{name}")
def get_metric(name: str, db: Annotated[Session, Depends(get_db)]):
    """
    Return a single metric definition.
    """

    m = db.execute(select(Metric).where(Metric.name == name)).scalar_one_or_none()
    if m is None:
        raise HTTPException(status_code=404, detail=f"Metric {name!r} not found")
    return {
        "name": m.name,
        "category": m.category,
        "description": m.description,
        "higher_is_better": m.higher_is_better,
        "threshold_warn": m.threshold_warn,
        "threshold_critical": m.threshold_critical,
    }
