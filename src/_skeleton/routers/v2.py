"""
V2 router, outside-in, consumer-facing .
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from checkup_api.database import get_db

router = APIRouter(prefix="/v2", tags=["v2"])


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

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Exercise 1: implement GET /v2/products",
    )


@router.get("/products/{slug}")
def get_product(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Return product detail.
    """

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Exercise 1: implement GET /v2/products/{slug}",
    )


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

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Exercise 1: implement GET /v2/products/{slug}/metrics",
    )


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

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Exercise 1: implement GET /v2/products/{slug}/metrics/{name}/history",
    )


@router.get("/metrics")
def list_metrics(
    db: Annotated[Session, Depends(get_db)],
    category: Annotated[str | None, Query()] = None,
):
    """List the metric catalog."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Exercise 1: implement GET /v2/metrics",
    )


@router.get("/metrics/{name}")
def get_metric(
    name: str,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Return a single metric definition.
    """

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Exercise 1: implement GET /v2/metrics/{name}",
    )
