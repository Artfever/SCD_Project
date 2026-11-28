"""Database tests run against a real Postgres, each session in its own schema.

They are skipped unless TEST_DATABASE_URL is set. CI sets it; locally use
`postgresql://postgres:<password>@127.0.0.1:5433/scd` with `docker compose up -d postgres`.
"""

import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest

from src.database import Database
from src.repository import Repository

URL = os.environ.get("TEST_DATABASE_URL", "")


@pytest.fixture
def repository() -> Iterator[Repository]:
    if not URL:
        pytest.skip("TEST_DATABASE_URL is not set")
    schema = f"test_{uuid.uuid4().hex}"
    with psycopg.connect(URL, autocommit=True) as admin:
        admin.execute(f"CREATE SCHEMA {schema}".encode())
    separator = "&" if "?" in URL else "?"
    dsn = f"{URL}{separator}options=-csearch_path%3D{schema}%2Cpublic"
    try:
        yield Repository(Database(dsn))
    finally:
        with psycopg.connect(URL, autocommit=True) as admin:
            admin.execute(f"DROP SCHEMA {schema} CASCADE".encode())
