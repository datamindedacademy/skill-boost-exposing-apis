"""
CheckUp FastAPI entrypoint.
"""

from fastapi import FastAPI

from checkup_api.routers import v1, v2

app = FastAPI(
    title="CheckUp API",
    description="Data product health metrics",
    version="0.1.0",
)

app.include_router(v1.router)
app.include_router(v2.router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
