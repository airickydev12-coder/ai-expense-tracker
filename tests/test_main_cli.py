"""Integration tests for the primary CLI controller."""

from collections.abc import Callable

import pytest

from src.financial.goals.models import Goal
from src.presentation import cli


InputFunction = Callable[[str], str]


def configure_cli_test(
    monkeypatch: pytest.MonkeyPatch,
    choices: list[str],
) -> None:
    """Configure shared primary-CLI dependencies."""
    choice_iterator = iter(choices)

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(choice_iterator),
    )

    monkeypatch.setattr(
        cli,
        "load_financial_state",
        lambda: None,
    )

    monkeypatch.setattr(
        cli,
        "register_default_scenario_handlers",
        lambda: None,
    )

    monkeypatch.setattr(
        cli,
        "display_dashboard",
        lambda: None,
    )

    monkeypatch.setattr(
        cli,
        "show_main_menu",
        lambda: None,
    )


def test_run_cli_initializes_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "16",
    )

    monkeypatch.setattr(
        cli,
        "load_financial_state",
        lambda: calls.append("load_financial_state"),
    )

    monkeypatch.setattr(
        cli,
        "register_default_scenario_handlers",
        lambda: calls.append("register_scenario_handlers"),
    )

    monkeypatch.setattr(
        cli,
        "display_dashboard",
        lambda: calls.append("display_dashboard"),
    )

    monkeypatch.setattr(
        cli,
        "show_main_menu",
        lambda: None,
    )

    cli.run_cli()

    assert calls == [
        "load_financial_state",
        "register_scenario_handlers",
        "display_dashboard",
    ]


def test_run_cli_routes_add_expense(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "1",
            "16",
        ],
    )

    def fake_add_expense_flow() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "add_expense_flow",
        fake_add_expense_flow,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_view_expenses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "2",
            "16",
        ],
    )

    def fake_display_expenses() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "display_expenses",
        fake_display_expenses,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_total_spending(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    expenses = [
        object(),
        object(),
    ]

    configure_cli_test(
        monkeypatch,
        [
            "3",
            "16",
        ],
    )

    monkeypatch.setattr(
        cli,
        "get_expenses",
        lambda: expenses,
    )

    monkeypatch.setattr(
        cli,
        "get_total",
        lambda received_expenses: (125.75 if received_expenses is expenses else 0.0),
    )

    cli.run_cli()

    output = capsys.readouterr().out

    assert "Total spending: $125.75" in output


def test_run_cli_routes_delete_expense(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "4",
            "16",
        ],
    )

    def fake_delete_expense_flow() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "delete_expense_flow",
        fake_delete_expense_flow,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_update_expense(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "5",
            "16",
        ],
    )

    def fake_update_expense_flow() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "update_expense_flow",
        fake_update_expense_flow,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_category_totals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "6",
            "16",
        ],
    )

    def fake_display_category_totals() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "display_category_totals",
        fake_display_category_totals,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_budget_management(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "7",
            "16",
        ],
    )

    def fake_manage_budgets() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "manage_budgets",
        fake_manage_budgets,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_budget_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "8",
            "16",
        ],
    )

    def fake_display_saved_budget_summaries() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "display_saved_budget_summaries",
        fake_display_saved_budget_summaries,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_records_financial_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    configure_cli_test(
        monkeypatch,
        [
            "9",
            "16",
        ],
    )

    snapshot = {
        "total_income": 5000,
    }

    monkeypatch.setattr(
        cli,
        "record_current_financial_snapshot",
        lambda: (
            snapshot,
            "record",
        ),
    )

    def fake_display_financial_snapshot(
        received_snapshot: dict,
    ) -> None:
        captured["snapshot"] = received_snapshot

    monkeypatch.setattr(
        cli,
        "display_financial_snapshot",
        fake_display_financial_snapshot,
    )

    cli.run_cli()

    assert captured["snapshot"] == snapshot


def test_run_cli_routes_recommendation_management(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "10",
            "16",
        ],
    )

    def fake_manage_recommendations() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "manage_recommendations",
        fake_manage_recommendations,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_financial_trends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    configure_cli_test(
        monkeypatch,
        [
            "11",
            "16",
        ],
    )

    history = [
        "snapshot",
    ]

    monkeypatch.setattr(
        cli,
        "get_history",
        lambda: history,
    )

    def fake_display_financial_trends(
        received_history: list[str],
    ) -> None:
        captured["history"] = received_history

    monkeypatch.setattr(
        cli,
        "display_financial_trends",
        fake_display_financial_trends,
    )

    cli.run_cli()

    assert captured["history"] == history


def test_run_cli_routes_forecast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "12",
            "16",
        ],
    )

    def fake_display_current_forecast() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "display_current_forecast",
        fake_display_current_forecast,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_scenario_management(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "13",
            "16",
        ],
    )

    def fake_manage_scenarios() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "manage_scenarios",
        fake_manage_scenarios,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_financial_coach(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "14",
            "16",
        ],
    )

    def fake_run_financial_coach() -> None:
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "run_financial_coach",
        fake_run_financial_coach,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_goal_planner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goals = [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=10000.0,
            current_amount=2500.0,
        ),
        Goal(
            id=2,
            name="Vacation",
            target_amount=3000.0,
            current_amount=500.0,
        ),
    ]

    captured: dict[str, object] = {}

    configure_cli_test(
        monkeypatch,
        [
            "15",
            "16",
        ],
    )

    monkeypatch.setattr(
        cli,
        "get_goals",
        lambda: goals,
    )

    def fake_run_goal_planning_menu(
        received_goals: list[Goal],
    ) -> None:
        captured["goals"] = received_goals

    monkeypatch.setattr(
        cli,
        "run_goal_planning_menu",
        fake_run_goal_planning_menu,
    )

    cli.run_cli()

    assert captured["goals"] is goals


def test_run_cli_gets_fresh_goals_each_time_planner_opens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_goals = [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=10000.0,
            current_amount=2000.0,
        ),
    ]

    second_goals = [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=10000.0,
            current_amount=3000.0,
        ),
    ]

    goal_results = iter(
        [
            first_goals,
            second_goals,
        ]
    )

    received_goal_lists: list[list[Goal]] = []

    configure_cli_test(
        monkeypatch,
        [
            "15",
            "15",
            "16",
        ],
    )

    monkeypatch.setattr(
        cli,
        "get_goals",
        lambda: next(goal_results),
    )

    monkeypatch.setattr(
        cli,
        "run_goal_planning_menu",
        lambda goals: (received_goal_lists.append(goals)),
    )

    cli.run_cli()

    assert received_goal_lists == [
        first_goals,
        second_goals,
    ]


def test_run_cli_passes_empty_goal_list_to_planner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    configure_cli_test(
        monkeypatch,
        [
            "15",
            "16",
        ],
    )

    monkeypatch.setattr(
        cli,
        "get_goals",
        lambda: [],
    )

    monkeypatch.setattr(
        cli,
        "run_goal_planning_menu",
        lambda goals: captured.update(goals=goals),
    )

    cli.run_cli()

    assert captured["goals"] == []


def test_run_cli_exits_with_option_16(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_cli_test(
        monkeypatch,
        [
            "16",
        ],
    )

    cli.run_cli()

    output = capsys.readouterr().out

    assert "Goodbye!" in output


def test_run_cli_rejects_invalid_option(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_cli_test(
        monkeypatch,
        [
            "invalid",
            "16",
        ],
    )

    cli.run_cli()

    output = capsys.readouterr().out

    assert "Invalid option." in output
    assert "1 through 16" in output
