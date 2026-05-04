"""
Tests for Exercise 3.
"""

from __future__ import annotations

import pytest

from checkup_api.main import app

V2_SCHEMAS = {
    "ProductSummary",
    "ProductDetail",
    "MetricStatus",
    "MetricHistoryPoint",
    "MetricCatalogEntry",
    "HealthRollup",
}

V2_OPERATIONS = [
    ("get", "/v2/products"),
    ("get", "/v2/products/{slug}"),
    ("get", "/v2/products/{slug}/metrics"),
    ("get", "/v2/products/{slug}/metrics/{name}/history"),
    ("get", "/v2/metrics"),
    ("get", "/v2/metrics/{name}"),
]


@pytest.fixture
def spec():
    app.openapi_schema = None  # force regeneration
    return app.openapi()


def _resolve_enum(spec, prop):
    """OpenAPI emits Literals as a referenced component; resolve through $ref."""
    ref = prop.get("$ref") or (
        prop.get("allOf", [{}])[0].get("$ref") if prop.get("allOf") else None
    )
    if not ref:
        return None
    name = ref.rsplit("/", 1)[-1]
    target = spec["components"]["schemas"].get(name, {})
    return target.get("enum")


class TestApiInfo:
    def test_has_description(self, spec):
        info = spec["info"]
        assert info["description"], "FastAPI app description is empty"
        assert len(info["description"]) > 100, (
            "API description is too short to be useful"
        )

    def test_has_proper_version(self, spec):
        assert spec["info"]["version"] != "0.1.0", (
            "version is still the scaffold default — bump it to signal real release"
        )


class TestSchemas:
    def test_every_v2_schema_has_description(self, spec):
        schemas = spec["components"]["schemas"]
        for name in V2_SCHEMAS:
            assert name in schemas, f"schema {name} missing from spec"
            assert schemas[name].get("description"), f"schema {name} has no description"

    def test_every_v2_field_has_description(self, spec):
        schemas = spec["components"]["schemas"]
        missing: list[str] = []
        for name in V2_SCHEMAS:
            for field, prop in schemas[name].get("properties", {}).items():
                if not prop.get("description"):
                    missing.append(f"{name}.{field}")
        assert not missing, "fields without description: " + ", ".join(missing)

    def test_every_v2_field_has_examples(self, spec):
        schemas = spec["components"]["schemas"]
        missing: list[str] = []
        for name in V2_SCHEMAS:
            for field, prop in schemas[name].get("properties", {}).items():
                has_example = bool(prop.get("examples")) or "example" in prop
                # Nested objects (HealthRollup) reference $ref — examples optional there
                if prop.get("$ref") or prop.get("allOf"):
                    continue
                if not has_example:
                    missing.append(f"{name}.{field}")
        assert not missing, "fields without examples: " + ", ".join(missing)

    def test_status_field_is_enum(self, spec):
        """Status should be `Literal['healthy','warn','critical']` so agents
        know the valid values, not a free-form string."""
        schemas = spec["components"]["schemas"]
        metric_status = schemas["MetricStatus"]
        status_prop = metric_status["properties"]["status"]
        enum_values = status_prop.get("enum") or _resolve_enum(spec, status_prop)
        assert enum_values, "MetricStatus.status is not an enum"
        assert set(enum_values) == {"healthy", "warn", "critical"}


class TestOperations:
    def test_every_v2_operation_has_summary(self, spec):
        for method, path in V2_OPERATIONS:
            op = spec["paths"][path][method]
            assert op.get("summary"), f"{method.upper()} {path} has no summary"

    def test_every_v2_operation_has_description(self, spec):
        for method, path in V2_OPERATIONS:
            op = spec["paths"][path][method]
            desc = op.get("description") or ""
            assert len(desc) > 50, (
                f"{method.upper()} {path} description is too short ({len(desc)} chars)"
            )

    def test_every_v2_operation_has_tags(self, spec):
        for method, path in V2_OPERATIONS:
            op = spec["paths"][path][method]
            assert op.get("tags"), f"{method.upper()} {path} has no tags"


class TestProductsListParams:
    """The /v2/products endpoint is the heaviest one for agents — give its
    parameters and response shape the most attention."""

    def test_params_documented(self, spec):
        params = {
            p["name"]: p
            for p in spec["paths"]["/v2/products"]["get"].get("parameters", [])
        }
        for required in ("entity", "status", "sort", "limit", "offset"):
            assert required in params, f"/v2/products missing param {required!r}"
            assert params[required].get("description"), (
                f"/v2/products param {required!r} has no description"
            )

    def test_has_response_model(self, spec):
        op = spec["paths"]["/v2/products"]["get"]
        response_200 = op["responses"]["200"]
        content = response_200.get("content", {})
        assert "application/json" in content
        schema = content["application/json"].get("schema", {})
        # Should reference ProductSummary (either as array of $ref or with items)
        items = schema.get("items", {})
        ref = items.get("$ref") or schema.get("$ref")
        assert ref and ref.endswith("ProductSummary"), (
            f"/v2/products GET should declare response_model=list[ProductSummary], got {schema}"
        )
