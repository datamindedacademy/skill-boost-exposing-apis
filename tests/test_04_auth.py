"""
Tests for Exercise 4.
"""

from __future__ import annotations


def test_no_token_is_rejected(client):
    """Without an Authorization header, FastAPI's HTTPBearer raises 403."""
    response = client.get("/v2/products")
    assert response.status_code in (401, 403)


def test_wildcard_scope_returns_all_products(client, auth_all_products):
    response = client.get("/v2/products")
    assert response.status_code == 200
    slugs = sorted(p["slug"] for p in response.json())
    assert slugs == [
        "cosmic_inventory",
        "nebula_customers",
        "quantum_marketing",
        "stellar_sales",
    ]


def test_scoped_token_filters_products(client, auth_only_stellar):
    response = client.get("/v2/products")
    assert response.status_code == 200
    slugs = [p["slug"] for p in response.json()]
    assert slugs == ["stellar_sales"]


def test_scoped_token_can_access_allowed_product(client, auth_only_stellar):
    response = client.get("/v2/products/stellar_sales")
    assert response.status_code == 200
    assert response.json()["slug"] == "stellar_sales"


def test_scoped_token_cannot_access_forbidden_product(client, auth_only_stellar):
    """A scoped agent asking for a product outside its scope gets 404 (or 403).
    The product exists, but should look not-found from this caller's view."""
    response = client.get("/v2/products/cosmic_inventory")
    assert response.status_code in (403, 404)


def test_scoped_token_filters_metrics_listing(client, auth_only_stellar):
    """Listing metrics on a forbidden product should also be denied."""
    response = client.get("/v2/products/cosmic_inventory/metrics")
    assert response.status_code in (403, 404)
