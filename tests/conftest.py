import pytest


@pytest.fixture
def db_path(tmp_path):
    """Return a throwaway SQLite database path for repository tests."""
    return tmp_path / "test.db"
