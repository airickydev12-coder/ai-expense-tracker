import pytest

from src.core.db import clear_test_database, initialize_database, set_test_database


@pytest.fixture
def db_path(tmp_path):
    """Return a throwaway SQLite database path for repository tests."""
    return tmp_path / "test.db"


@pytest.fixture(autouse=True)
def _stub_email_sending(monkeypatch: pytest.MonkeyPatch):
    """Prevent every test from making a real SMTP call by default.

    register_user() sends a verification email automatically now -- without
    this, a real, fully-configured .env (this repo's local dev one has real
    Gmail credentials, used for the LAN deployment) would make the test
    suite send a real email on every single registration across the whole
    suite, hitting a real inbox hundreds of times per run and roughly
    doubling suite runtime on real SMTP round-trips. Individual tests that
    need to inspect what would have been sent (e.g. the forgot-password
    tests) already call `monkeypatch.setattr(user_service,
    "send_notification_email", ...)` themselves -- that call simply
    overrides this default within that one test, no conflict.
    """
    monkeypatch.setattr(
        "src.financial.users.service.send_notification_email",
        lambda subject, body, to_email=None: None,
    )


@pytest.fixture(autouse=True)
def _stub_breach_check(monkeypatch: pytest.MonkeyPatch):
    """Prevent every test from making a real HIBP network call by default.

    register/change-password/reset-password all call is_password_breached()
    now -- without this, hundreds of test registrations across the whole
    suite would each make a real HTTP call to api.pwnedpasswords.com,
    slowing the suite and making it depend on network access. Individual
    tests that need to exercise the actual breach-found/breach-check-failed
    paths override this themselves via `monkeypatch.setattr(auth_router,
    "is_password_breached", ...)`, the same way `_stub_email_sending` works
    above.
    """
    monkeypatch.setattr(
        "src.api.routers.auth.is_password_breached",
        lambda password: False,
    )


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
