"""
V2 router, outside-in, consumer-facing.

Exercise 3 solution: routes annotated with summary/tags/response_model and
rich docstrings; query params Annotated with descriptions and examples.
"""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from checkup_api.database import get_db
from checkup_api.models import Entity, Measurement, Metric, Product
from checkup_api.schemas import (
    HealthRollup,
    MetricCatalogEntry,
    MetricHistoryPoint,
    MetricStatus,
    ProductDetail,
    ProductSummary,
)

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


def _rollup_for_product(p: Product) -> HealthRollup:
    counts = {"healthy": 0, "warn": 0, "critical": 0}
    for m in _latest_per_metric(list(p.measurements)):
        s = _compute_status(m.value, m.metric.higher_is_better, m.metric.threshold_warn, m.metric.threshold_critical)
        if s in counts:
            counts[s] += 1
    return HealthRollup(**counts)


@router.get(
    "/products",
    response_model=list[ProductSummary],
    summary="List data products",
)
def list_products(
    db: Annotated[Session, Depends(get_db)],
    entity: Annotated[
        str | None,
        Query(
            description="Filter to products owned by this entity (slug). Example: `marketing`.",
            examples=["analytics"],
        ),
    ] = None,
    status_filter: Annotated[
        Literal["healthy", "warn", "critical"] | None,
        Query(
            alias="status",
            description=(
                "Keep products that have at least one metric in this status bucket. "
                "Combine with `sort=health` to surface the worst offenders first."
            ),
        ),
    ] = None,
    sort: Annotated[
        Literal["name", "health"] | None,
        Query(description="Sort order. Default is by `name` ascending. `health` puts most-critical first."),
    ] = None,
    limit: Annotated[
        int,
        Query(description="Maximum number of items to return (default 25, max 100).", ge=1, le=100),
    ] = 25,
    offset: Annotated[
        int,
        Query(description="How many items to skip — for pagination.", ge=0),
    ] = 0,
):
    """List all data products with their owning entity and a current health rollup.

    Each item embeds `{healthy, warn, critical}` counts so a single call is
    enough to render a dashboard view. Default sort is by product name; pass
    `sort=health` to put products with critical metrics first. Pagination is
    via `limit` and `offset`.
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

    items: list[ProductSummary] = []
    for p in products:
        health = _rollup_for_product(p)
        if status_filter and getattr(health, status_filter) == 0:
            continue
        items.append(
            ProductSummary(
                slug=p.slug,
                name=p.name,
                entity=p.entity.name,
                owner_email=p.owner_email,
                health=health,
            )
        )

    if sort == "health":
        items.sort(key=lambda x: (x.health.critical, x.health.warn), reverse=True)

    return items[offset : offset + limit]


@router.get(
    "/products/{slug}",
    response_model=ProductDetail,
    summary="Get a product by slug",
)
def get_product(slug: str, db: Annotated[Session, Depends(get_db)]):
    """Return the full attributes of a single product plus its health rollup.
    Returns 404 if no product matches the slug.
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

    return ProductDetail(
        slug=p.slug,
        name=p.name,
        entity=p.entity.name,
        owner_email=p.owner_email,
        created_at=p.created_at,
        health=_rollup_for_product(p),
    )


@router.get(
    "/products/{slug}/metrics",
    response_model=list[MetricStatus],
    summary="List a product's current metrics",
)
def list_product_metrics(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    category: Annotated[
        Literal["data_quality", "freshness", "infrastructure", "dbt"] | None,
        Query(description="Filter to metrics in this category."),
    ] = None,
    status_filter: Annotated[
        Literal["healthy", "warn", "critical"] | None,
        Query(alias="status", description="Filter by derived status."),
    ] = None,
):
    """For each metric tracked on this product, return its latest value with
    a server-derived `status` (healthy/warn/critical) computed from the
    metric's thresholds. The thresholds themselves live in the catalog
    (see `/v2/metrics/{name}`); clients don't need to fetch them to interpret
    a status.
    """
    stmt = (
        select(Product)
        .options(selectinload(Product.measurements).selectinload(Measurement.metric))
        .where(Product.slug == slug)
    )
    p = db.execute(stmt).unique().scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail=f"Product {slug!r} not found")

    items: list[MetricStatus] = []
    for m in _latest_per_metric(list(p.measurements)):
        if category and m.metric.category != category:
            continue
        s = _compute_status(m.value, m.metric.higher_is_better, m.metric.threshold_warn, m.metric.threshold_critical)
        if status_filter and s != status_filter:
            continue
        items.append(
            MetricStatus(
                name=m.name,
                category=m.metric.category,
                value=m.value,
                unit=m.unit,
                status=s,
                measured_at=m.measured_at,
                diagnostic=m.diagnostic,
            )
        )
    return items


@router.get(
    "/products/{slug}/metrics/{name}/history",
    response_model=list[MetricHistoryPoint],
    summary="Time series for a single metric on a product",
)
def get_metric_history(
    slug: str,
    name: str,
    db: Annotated[Session, Depends(get_db)],
    since: Annotated[
        datetime | None,
        Query(description="Only return points measured at or after this ISO-8601 timestamp."),
    ] = None,
    limit: Annotated[
        int,
        Query(description="Maximum number of points to return (default 100, max 500).", ge=1, le=500),
    ] = 100,
):
    """Return the historical measurements for one metric on one product,
    most recent first. Each point includes the raw value, when it was
    measured, and the derived status at that moment.
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
        MetricHistoryPoint(
            value=m.value,
            measured_at=m.measured_at,
            status=_compute_status(m.value, m.metric.higher_is_better, m.metric.threshold_warn, m.metric.threshold_critical),
        )
        for m in measurements
    ]


@router.get(
    "/metrics",
    response_model=list[MetricCatalogEntry],
    summary="List metric definitions in the catalog",
)
def list_metrics(
    db: Annotated[Session, Depends(get_db)],
    category: Annotated[
        Literal["data_quality", "freshness", "infrastructure", "dbt"] | None,
        Query(description="Filter the catalog to metrics in this category."),
    ] = None,
):
    """Return all metric definitions in the catalog. Each entry describes
    what the metric means, whether higher or lower values are better, and
    the warn/critical thresholds used to derive a status.
    """
    stmt = select(Metric)
    if category:
        stmt = stmt.where(Metric.category == category)
    return db.execute(stmt).scalars().all()


@router.get(
    "/metrics/{name}",
    response_model=MetricCatalogEntry,
    summary="Get a metric definition",
)
def get_metric(name: str, db: Annotated[Session, Depends(get_db)]):
    """Return a single metric's definition, including thresholds. Returns
    404 if the metric is not in the catalog.
    """
    m = db.execute(select(Metric).where(Metric.name == name)).scalar_one_or_none()
    if m is None:
        raise HTTPException(status_code=404, detail=f"Metric {name!r} not found")
    return m
