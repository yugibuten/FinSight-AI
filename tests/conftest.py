import os

import pytest

# Tests use one shared in-memory SQLite connection and never touch local data.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.cache import response_cache, tool_cache
from app.db.database import Base, engine, init_database


@pytest.fixture(autouse=True)
def clear_application_caches():
    Base.metadata.drop_all(bind=engine)
    init_database()
    response_cache.clear()
    tool_cache.clear()
    yield
    response_cache.clear()
    tool_cache.clear()
