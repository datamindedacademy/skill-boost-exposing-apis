"""
V1 router, inside-out, DB-mirroring.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from checkup_api.database import get_db
from checkup_api.schemas import EntityRow, MeasurementRow, MetricRow, ProductRow

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/entities", response_model=list[EntityRow])
def list_entities(db: Annotated[Session, Depends(get_db)]):
    rows = db.execute(text("SELECT id, name, slug FROM entities")).mappings().all()
    return list(rows)


@router.get("/products", response_model=list[ProductRow])
def list_products(
    db: Annotated[Session, Depends(get_db)],
    entity_id: Annotated[int | None, Query()] = None,
):
    sql = "SELECT id, name, slug, entity_id, owner_email, created_at FROM products"
    params: dict = {}
    if entity_id is not None:
        sql += " WHERE entity_id = :entity_id"
        params["entity_id"] = entity_id
    rows = db.execute(text(sql), params).mappings().all()
    return list(rows)


@router.get("/metrics", response_model=list[MetricRow])
def list_metrics(db: Annotated[Session, Depends(get_db)]):
    rows = (
        db.execute(
            text(
                "SELECT id, name, category, description, higher_is_better, "
                "threshold_warn, threshold_critical FROM metrics"
            )
        )
        .mappings()
        .all()
    )
    return list(rows)


@router.get("/measurements", response_model=list[MeasurementRow])
def list_measurements(
    db: Annotated[Session, Depends(get_db)],
    tag_product: Annotated[str | None, Query()] = None,
    name: Annotated[str | None, Query()] = None,
):
    sql = (
        "SELECT name, value, unit, diagnostic, description, "
        "tag_entity, tag_pbac_prefix, tag_product, measured_at FROM measurements"
    )
    clauses: list[str] = []
    params: dict = {}
    if tag_product:
        clauses.append("tag_product = :tag_product")
        params["tag_product"] = tag_product
    if name:
        clauses.append("name = :name")
        params["name"] = name
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    rows = db.execute(text(sql), params).mappings().all()
    return list(rows)
