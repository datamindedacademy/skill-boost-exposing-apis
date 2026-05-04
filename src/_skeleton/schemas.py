"""
Pydantic schemas for the v1 and v2 API.

TODO: These are sparse: no Field descriptions, no examples, no enums.
"""

from datetime import datetime

from pydantic import BaseModel


class EntityRow(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class ProductRow(BaseModel):
    id: int
    name: str
    slug: str
    entity_id: int
    owner_email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricRow(BaseModel):
    id: int
    name: str
    category: str
    description: str | None
    higher_is_better: bool
    threshold_warn: float | None
    threshold_critical: float | None

    model_config = {"from_attributes": True}


class MeasurementRow(BaseModel):
    name: str
    value: str | None
    unit: str | None
    diagnostic: str | None
    description: str | None
    tag_entity: str | None
    tag_pbac_prefix: str | None
    tag_product: str
    measured_at: datetime

    model_config = {"from_attributes": True}


class HealthRollup(BaseModel):
    healthy: int
    warn: int
    critical: int


class ProductSummary(BaseModel):
    slug: str
    name: str
    entity: str
    owner_email: str
    health: HealthRollup


class ProductDetail(BaseModel):
    slug: str
    name: str
    entity: str
    owner_email: str
    created_at: datetime
    health: HealthRollup


class MetricStatus(BaseModel):
    name: str
    category: str
    value: str | None
    unit: str | None
    status: str
    measured_at: datetime
    diagnostic: str | None


class MetricHistoryPoint(BaseModel):
    value: str | None
    measured_at: datetime
    status: str


class MetricCatalogEntry(BaseModel):
    name: str
    category: str
    description: str | None
    higher_is_better: bool
    threshold_warn: float | None
    threshold_critical: float | None
