"""
CheckUp FastAPI entrypoint.

Exercise 3 solution: title, description, and version filled in for OpenAPI.
"""

from fastapi import FastAPI

from checkup_api.routers import v1, v2

app = FastAPI(
    title="CheckUp API",
    description=(
        "Health metrics for our data products.\n\n"
        "## Concepts\n"
        "- **Product**: a data product registered with the Checkup tool. Identified by `slug`.\n"
        "- **Entity**: the team or department that owns one or more products.\n"
        "- **Metric**: a quantitative health indicator, with a category, unit, and thresholds.\n"
        "- **Status**: derived per measurement from the metric's thresholds — `healthy`, `warn`, or `critical`.\n\n"
        "## Versions\n"
        "- `/v1/*` is the legacy DB-mirroring API. Avoid it for new integrations.\n"
        "- `/v2/*` is the consumer-facing API.\n\n"
        "## Common flows\n"
        "- Dashboard view: `GET /v2/products` returns each product's health rollup in one call.\n"
        "- Drill-down: `GET /v2/products/{slug}/metrics` lists per-metric status.\n"
        "- Trends: `GET /v2/products/{slug}/metrics/{name}/history` returns the time series.\n"
    ),
    version="2.0.0",
)

app.include_router(v1.router)
app.include_router(v2.router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
