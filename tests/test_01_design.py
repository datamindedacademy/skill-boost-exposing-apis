"""
Tests for Exercise 1.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.usefixtures("auth_all_products")


class TestListProducts:
    def test_returns_summaries_with_entity_and_health(self, client):
        response = client.get("/v2/products")
        assert response.status_code == 200, response.text
        items = response.json()
        assert isinstance(items, list)
        assert len(items) == 4

        item = next(p for p in items if p["slug"] == "stellar_sales")
        assert item["name"] == "Stellar Sales"
        assert item["entity"] == "Analytics"
        assert item["owner_email"] == "stellar.sales@example.com"
        assert item["health"] == {"healthy": 6, "warn": 0, "critical": 3}

    def test_filters_by_entity(self, client):
        response = client.get("/v2/products?entity=marketing")
        assert response.status_code == 200
        slugs = [p["slug"] for p in response.json()]
        assert slugs == ["quantum_marketing"]

    def test_filters_by_status(self, client):
        """`status` filter keeps products with at least one metric in that bucket."""
        response = client.get("/v2/products?status=critical")
        assert response.status_code == 200
        slugs = sorted(p["slug"] for p in response.json())
        # stellar_sales (33% coverage), quantum_marketing (12%, 45 days, minerva=0)
        assert slugs == ["quantum_marketing", "stellar_sales"]

    def test_pagination(self, client):
        page1 = client.get("/v2/products?limit=2&offset=0").json()
        page2 = client.get("/v2/products?limit=2&offset=2").json()
        assert len(page1) == 2
        assert len(page2) == 2
        assert {p["slug"] for p in page1}.isdisjoint({p["slug"] for p in page2})


class TestGetProduct:
    def test_returns_detail(self, client):
        response = client.get("/v2/products/cosmic_inventory")
        assert response.status_code == 200
        body = response.json()
        assert body["slug"] == "cosmic_inventory"
        assert body["name"] == "Cosmic Inventory"
        assert body["entity"] == "Operations"
        assert body["owner_email"] == "cosmic.inventory@example.com"
        assert body["health"] == {"healthy": 7, "warn": 2, "critical": 0}

    def test_returns_404_for_unknown_slug(self, client):
        response = client.get("/v2/products/does_not_exist")
        assert response.status_code == 404


class TestProductMetrics:
    def test_derives_status_server_side(self, client):
        """Status is computed server-side from thresholds (the inside-out API
        forced the client to do this)."""
        response = client.get("/v2/products/stellar_sales/metrics")
        assert response.status_code == 200
        by_name = {m["name"]: m for m in response.json()}

        # higher_is_better=True, warn=80, critical=50, value=33  -> critical
        assert by_name["dbt_column_test_coverage"]["status"] == "critical"
        assert by_name["dbt_column_test_coverage"]["category"] == "data_quality"

        # higher_is_better=False, warn=10, critical=30, value=45 -> critical
        assert by_name["dbt_models_without_description"]["status"] == "critical"

        # higher_is_better=False, warn=7, critical=30, value=1 -> healthy
        assert by_name["git_days_since_last_update"]["status"] == "healthy"

        # boolean: higher=True, warn=critical=1, value=1 -> healthy
        assert by_name["minerva_config_exists"]["status"] == "healthy"

    def test_status_warn_band(self, client):
        response = client.get("/v2/products/cosmic_inventory/metrics")
        by_name = {m["name"]: m for m in response.json()}
        # coverage=78, warn=80 critical=50, higher_is_better=True -> warn (50<=v<80)
        assert by_name["dbt_column_test_coverage"]["status"] == "warn"
        # git_days=15, warn=7 critical=30, higher=False -> warn (7<v<=30)
        assert by_name["git_days_since_last_update"]["status"] == "warn"

    def test_filter_by_category(self, client):
        response = client.get(
            "/v2/products/stellar_sales/metrics?category=data_quality"
        )
        assert response.status_code == 200
        items = response.json()
        assert all(m["category"] == "data_quality" for m in items)
        assert any(m["name"] == "dbt_column_test_coverage" for m in items)

    def test_filter_by_status(self, client):
        response = client.get("/v2/products/quantum_marketing/metrics?status=critical")
        assert response.status_code == 200
        statuses = {m["status"] for m in response.json()}
        assert statuses == {"critical"}


class TestMetricHistory:
    def test_returns_time_series(self, client):
        response = client.get(
            "/v2/products/stellar_sales/metrics/dbt_column_test_coverage/history"
        )
        assert response.status_code == 200
        points = response.json()
        # 4 measurements: current (33) + 3 historical (28, 25, 20)
        assert len(points) == 4
        # most recent first
        timestamps = [p["measured_at"] for p in points]
        assert timestamps == sorted(timestamps, reverse=True)
        assert points[0]["value"] == "33"
        assert points[0]["status"] == "critical"


class TestMetricCatalog:
    def test_list(self, client):
        response = client.get("/v2/metrics")
        assert response.status_code == 200
        names = {m["name"] for m in response.json()}
        assert "dbt_column_test_coverage" in names
        assert "git_days_since_last_update" in names

    def test_filter_by_category(self, client):
        response = client.get("/v2/metrics?category=freshness")
        items = response.json()
        assert all(m["category"] == "freshness" for m in items)
        assert any(m["name"] == "git_days_since_last_update" for m in items)

    def test_get_entry(self, client):
        response = client.get("/v2/metrics/dbt_column_test_coverage")
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "dbt_column_test_coverage"
        assert body["category"] == "data_quality"
        assert bool(body["higher_is_better"]) is True
        assert float(body["threshold_warn"]) == 80
        assert float(body["threshold_critical"]) == 50

    def test_get_entry_404(self, client):
        response = client.get("/v2/metrics/does_not_exist")
        assert response.status_code == 404
