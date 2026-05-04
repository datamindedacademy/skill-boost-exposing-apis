"""
SQLAlchemy ORM models.

Exercise 2 solution: relationships added, including natural-key joins.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from checkup_api.database import Base


class Entity(Base):
    """
    Business entity / department.
    """

    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)


class Product(Base):
    """
    A data product.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"))
    owner_email: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime)

    entity: Mapped["Entity"] = relationship("Entity")

    # Natural-key relationship: measurements.tag_product = products.slug.
    # No FK constraint in the DB, so foreign() marks the "many" side and
    # viewonly=True disables cascade behavior.
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement",
        primaryjoin="Product.slug == foreign(Measurement.tag_product)",
        viewonly=True,
    )


class Metric(Base):
    """
    Metric definition.
    """

    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    category: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    higher_is_better: Mapped[bool] = mapped_column(Boolean)
    threshold_warn: Mapped[float | None] = mapped_column(Numeric)
    threshold_critical: Mapped[float | None] = mapped_column(Numeric)


class Measurement(Base):
    """
    Metric measurement.
    """

    __tablename__ = "measurements"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    tag_product: Mapped[str] = mapped_column(String(255), primary_key=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime, primary_key=True)

    value: Mapped[str | None] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(255))
    diagnostic: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    tag_entity: Mapped[str | None] = mapped_column(String(255))
    tag_pbac_prefix: Mapped[str | None] = mapped_column(String(255))

    # Natural-key relationship: measurements.name = metrics.name.
    metric: Mapped["Metric"] = relationship(
        "Metric",
        primaryjoin="Measurement.name == foreign(Metric.name)",
        viewonly=True,
    )
