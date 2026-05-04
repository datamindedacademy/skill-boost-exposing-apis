"""
Pydantic schemas for the v1 and v2 API.

Exercise 3 solution: v2 schemas enriched with descriptions, examples, and
`Literal` enums. v1 stays sparse on purpose.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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
    """Count of metrics on a product, bucketed by status."""

    healthy: int = Field(description="Metrics meeting the healthy threshold", examples=[3])
    warn: int = Field(description="Metrics in the warning band", examples=[1])
    critical: int = Field(description="Metrics that breach the critical threshold", examples=[2])


class ProductSummary(BaseModel):
    """A data product summary suitable for list views and dashboards."""

    slug: str = Field(
        description="URL-safe identifier for the product. Use this in subsequent calls.",
        examples=["stellar_sales"],
    )
    name: str = Field(description="Human-readable product name", examples=["Stellar Sales"])
    entity: str = Field(
        description="Owning team or department (joined in from the entity dim)",
        examples=["Analytics"],
    )
    owner_email: str = Field(
        description="Primary contact for product-related questions",
        examples=["stellar.sales@example.com"],
    )
    health: HealthRollup = Field(description="Latest count of metrics by status")


class ProductDetail(BaseModel):
    """A data product with full attributes plus the health rollup."""

    slug: str = Field(description="URL-safe identifier", examples=["stellar_sales"])
    name: str = Field(description="Human-readable name", examples=["Stellar Sales"])
    entity: str = Field(description="Owning team or department", examples=["Analytics"])
    owner_email: str = Field(description="Primary contact", examples=["stellar.sales@example.com"])
    created_at: datetime = Field(
        description="When the product was registered with Checkup",
        examples=["2024-01-15T09:00:00"],
    )
    health: HealthRollup = Field(description="Latest count of metrics by status")


class MetricStatus(BaseModel):
    """A single metric's latest value, with a derived status from the catalog thresholds."""

    name: str = Field(
        description="Metric identifier as defined in the catalog (see /v2/metrics)",
        examples=["dbt_column_test_coverage"],
    )
    category: str = Field(
        description="Category of the metric (data_quality, freshness, infrastructure, dbt)",
        examples=["data_quality"],
    )
    value: str | None = Field(description="Latest measured value, as a string", examples=["33"])
    unit: str | None = Field(description="Unit of measurement", examples=["percent"])
    status: Literal["healthy", "warn", "critical"] = Field(
        description=(
            "Derived from the metric's thresholds. `healthy` means within tolerance, "
            "`warn` is between the warn and critical thresholds, `critical` breaches "
            "the critical threshold."
        ),
        examples=["critical"],
    )
    measured_at: datetime = Field(
        description="When this measurement was taken",
        examples=["2026-04-23T12:45:20"],
    )
    diagnostic: str | None = Field(
        description="Free-form diagnostic message from the Checkup tool, if any",
        examples=["Last commit: 2026-04-22"],
    )


class MetricHistoryPoint(BaseModel):
    """One point in a metric's time series for a product."""

    value: str | None = Field(description="Measured value at this point in time", examples=["33"])
    measured_at: datetime = Field(
        description="When the measurement was taken",
        examples=["2026-04-23T12:45:20"],
    )
    status: Literal["healthy", "warn", "critical"] = Field(
        description="Derived status at the time of measurement",
        examples=["critical"],
    )


class MetricCatalogEntry(BaseModel):
    """A metric definition: what it means, how to interpret it, and its thresholds."""

    name: str = Field(description="Metric identifier", examples=["dbt_column_test_coverage"])
    category: str = Field(
        description="Category of the metric (data_quality, freshness, infrastructure, dbt)",
        examples=["data_quality"],
    )
    description: str | None = Field(
        description="What this metric measures, in plain language",
        examples=["Percentage of columns with at least one test"],
    )
    higher_is_better: bool = Field(
        description="If true, higher values are better. Otherwise lower is better.",
        examples=[True],
    )
    threshold_warn: float | None = Field(
        description="Boundary between healthy and warn",
        examples=[80],
    )
    threshold_critical: float | None = Field(
        description="Boundary between warn and critical",
        examples=[50],
    )
