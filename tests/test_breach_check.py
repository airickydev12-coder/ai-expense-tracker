"""Tests for HaveIBeenPwned k-anonymity breached-password screening."""

import hashlib

import httpx
import pytest

from src.financial.users import breach_check


def _hash(password: str) -> tuple[str, str]:
    sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    return sha1_hash[:5], sha1_hash[5:]


def test_is_password_breached_returns_true_on_matching_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prefix, suffix = _hash("password123")

    def fake_request(sent_prefix: str) -> str:
        assert sent_prefix == prefix
        return f"{suffix}:3730471\nAAAA0000000000000000000000000000000:1\n"

    monkeypatch.setattr(breach_check, "_request_breach_range", fake_request)

    assert breach_check.is_password_breached("password123") is True


def test_is_password_breached_returns_false_when_suffix_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        breach_check,
        "_request_breach_range",
        lambda prefix: "AAAA0000000000000000000000000000000:1\n",
    )

    assert breach_check.is_password_breached("a-genuinely-unique-passphrase") is False


def test_is_password_breached_fails_open_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A network failure or non-2xx response must never raise -- it's
    treated as 'not known to be breached' so the caller's soft-warning flow
    never turns into a hard block."""

    def raise_error(prefix: str) -> str:
        raise httpx.ConnectTimeout("timed out")

    monkeypatch.setattr(breach_check, "_request_breach_range", raise_error)

    assert breach_check.is_password_breached("anything") is False


def test_request_breach_range_sends_only_the_hash_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """The full password (or its full hash) must never appear in the
    outgoing request -- only the 5-character prefix, per HIBP's
    k-anonymity contract."""
    captured: dict = {}

    class FakeResponse:
        text = "SOMESUFFIX:1\n"

        def raise_for_status(self) -> None:
            pass

    def fake_get(url: str, timeout: float, headers: dict) -> FakeResponse:
        captured["url"] = url
        return FakeResponse()

    monkeypatch.setattr(httpx, "get", fake_get)

    prefix, _suffix = _hash("hunter2")
    breach_check._request_breach_range(prefix)

    assert captured["url"].endswith(f"/{prefix}")
    assert "hunter2" not in captured["url"]
