"""
Tests for Exercise 2.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.usefixtures("auth_all_products")


def test_list_products_query_budget(client, query_counter):
    """`/v2/products` rolls up health across 4 products and 4 metrics each.
    Naive lazy loading would issue 1 + N (or worse) queries; selectinload
    or a single aggregate query keeps it bounded."""
    query_counter.clear()
    response = client.get("/v2/products")
    assert response.status_code == 200
    assert len(response.json()) == 4
    assert len(query_counter) <= 3, (
        f"expected ≤3 queries, got {len(query_counter)}:\n" + "\n".join(query_counter)
    )


def test_list_product_metrics_query_budget(client, query_counter):
    """`/v2/products/{slug}/metrics` joins measurements↔metrics catalog.
    Should be ≤3 queries (1 for product lookup, 1 for measurements+metrics)."""
    query_counter.clear()
    response = client.get("/v2/products/stellar_sales/metrics")
    assert response.status_code == 200
    assert len(query_counter) <= 3, (
        f"expected ≤3 queries, got {len(query_counter)}:\n" + "\n".join(query_counter)
    )


def test_metric_history_query_budget(client, query_counter):
    query_counter.clear()
    response = client.get(
        "/v2/products/stellar_sales/metrics/dbt_column_test_coverage/history"
    )
    assert response.status_code == 200
    assert len(query_counter) <= 3


# Functional sanity — the ORM rewrite must preserve Ex1 behavior.


def test_list_products_still_returns_summaries(client):
    items = client.get("/v2/products").json()
    by_slug = {p["slug"]: p for p in items}
    assert by_slug["stellar_sales"]["entity"] == "Analytics"
    assert by_slug["stellar_sales"]["health"] == {
        "healthy": 6,
        "warn": 0,
        "critical": 3,
    }


def test_list_product_metrics_still_derives_status(client):
    items = client.get("/v2/products/quantum_marketing/metrics").json()
    by_name = {m["name"]: m for m in items}
    assert by_name["dbt_column_test_coverage"]["status"] == "critical"
    assert by_name["dbt_models_without_description"]["status"] == "warn"
