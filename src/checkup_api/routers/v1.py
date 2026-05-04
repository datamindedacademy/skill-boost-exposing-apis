"""
V1 router, inside-out, DB-mirroring.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from checkup_api.database import get_db
from checkup_api.models import Entity, Measurement, Metric, Product
from checkup_api.schemas import EntityRow, MeasurementRow, MetricRow, ProductRow

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/entities", response_model=list[EntityRow])
def list_entities(db: Annotated[Session, Depends(get_db)]):
    return db.execute(select(Entity)).scalars().all()


@router.get("/products", response_model=list[ProductRow])
def list_products(
    db: Annotated[Session, Depends(get_db)],
    entity_id: Annotated[int | None, Query()] = None,
):
    stmt = select(Product)
    if entity_id is not None:
        stmt = stmt.where(Product.entity_id == entity_id)
    return db.execute(stmt).scalars().all()


@router.get("/metrics", response_model=list[MetricRow])
def list_metrics(db: Annotated[Session, Depends(get_db)]):
    return db.execute(select(Metric)).scalars().all()


@router.get("/measurements", response_model=list[MeasurementRow])
def list_measurements(
    db: Annotated[Session, Depends(get_db)],
    tag_product: Annotated[str | None, Query()] = None,
    name: Annotated[str | None, Query()] = None,
):
    stmt = select(Measurement)
    if tag_product:
        stmt = stmt.where(Measurement.tag_product == tag_product)
    if name:
        stmt = stmt.where(Measurement.name == name)
    return db.execute(stmt).scalars().all()
