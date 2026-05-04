from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from checkup_api.auth import get_allowed_products
from checkup_api.database import engine
from checkup_api.main import app


@pytest.fixture
def client():
    """
    FastAPI TestClient against the running app + Postgres.
    """

    return TestClient(app)


@pytest.fixture
def query_counter():
    """
    Counts SQL statements executed against the production engine.
    """

    statements: list[str] = []

    def _before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", _before_cursor_execute)
    yield statements
    event.remove(engine, "before_cursor_execute", _before_cursor_execute)


@pytest.fixture
def auth_all_products():
    """
    Override auth so all requests are scoped to all products.
    """

    app.dependency_overrides[get_allowed_products] = lambda: []
    yield
    app.dependency_overrides.pop(get_allowed_products, None)


@pytest.fixture
def auth_only_stellar():
    """
    Override auth so requests are scoped only to stellar_sales.
    """

    app.dependency_overrides[get_allowed_products] = lambda: ["stellar_sales"]
    yield
    app.dependency_overrides.pop(get_allowed_products, None)
