from datetime import datetime, timezone

from src.financial.history.models import FinancialSnapshotRecord
from src.presentation import cli


def build_history() -> list[FinancialSnapshotRecord]:
    """Create one historical snapshot for CLI testing."""
    return [
        FinancialSnapshotRecord(
            timestamp=datetime(
                2026,
                7,
                13,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            total_income=5000,
            total_expenses=1500,
            net_cash_flow=3500,
            total_account_balance=2000,
            total_goal_progress=2500,
            total_debt=1000,
            net_worth=3500,
            health_score=85,
            health_status="Excellent",
        )
    ]


def test_run_cli_displays_financial_trends(
    monkeypatch,
):
    captured: dict = {}

    choices = iter(
        [
            "11",
            "15",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(choices),
    )

    monkeypatch.setattr(
        cli,
        "load_financial_state",
        lambda: None,
    )

    monkeypatch.setattr(
        cli,
        "display_dashboard",
        lambda: None,
    )

    monkeypatch.setattr(
        cli,
        "show_menu",
        lambda: None,
    )

    monkeypatch.setattr(
        cli,
        "get_history",
        build_history,
    )

    def fake_display(history):
        captured["history"] = history

    monkeypatch.setattr(
        cli,
        "display_financial_trends",
        fake_display,
    )

    cli.run_cli()

    assert len(captured["history"]) == 1
    assert captured["history"][0].net_worth == 3500
