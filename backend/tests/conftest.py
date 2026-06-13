import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DATABASE_URL", "data/test_aegis.db")
os.environ.setdefault("IRONLABS_API_KEY", "test-key")

import db as _db


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def init_database(event_loop):
    event_loop.run_until_complete(_db.init_db())
