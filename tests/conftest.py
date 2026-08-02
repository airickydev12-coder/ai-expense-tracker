import pytest

from src.core.db import clear_test_database, initialize_database, set_test_database


@pytest.fixture
def db_path(tmp_path):
    """Return a throwaway SQLite database path for repository tests."""
    return tmp_path / "test.db"


@pytest.fixture(autouse=True)
def _isolate_default_database(request, tmp_path):
    """
    Redirect every caller relying on the default DB_PATH to an isolated
    per-test database, for API tests only.

    Repository tests already pass their own explicit db_path (the `db_path`
    fixture above, or their own tmp_path) and are unaffected either way —
    this only substitutes what "the default" resolves to, never an explicit
    choice. Scoped to test_api_*.py files specifically: API routers never
    override db_path, so without this they'd write straight through to the
    real data/app.db on every test run. Every other test file skips the
    (relatively expensive) database setup entirely.
    """
    if not request.node.path.name.startswith("test_api_"):
        yield
        return

    test_db_path = tmp_path / "test_app.db"
    initialize_database(test_db_path)
    set_test_database(test_db_path)
    yield
    clear_test_database()
