from src.presentation import cli


def configure_cli_test(
    monkeypatch,
    choices: list[str],
) -> None:
    """Configure shared main CLI mocks."""
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
        "display_dashboard",
        lambda: None,
    )

    monkeypatch.setattr(
        cli,
        "show_menu",
        lambda: None,
    )


def test_run_cli_routes_add_expense(
    monkeypatch,
):
    captured = {"called": False}

    configure_cli_test(
        monkeypatch,
        [
            "1",
            "15",
        ],
    )

    def fake_add_expense_flow():
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "add_expense_flow",
        fake_add_expense_flow,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_view_expenses(
    monkeypatch,
):
    captured = {"called": False}

    configure_cli_test(
        monkeypatch,
        [
            "2",
            "15",
        ],
    )

    def fake_display_expenses():
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "display_expenses",
        fake_display_expenses,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_delete_expense(
    monkeypatch,
):
    captured = {"called": False}

    configure_cli_test(
        monkeypatch,
        [
            "4",
            "15",
        ],
    )

    def fake_delete_expense_flow():
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "delete_expense_flow",
        fake_delete_expense_flow,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_update_expense(
    monkeypatch,
):
    captured = {"called": False}

    configure_cli_test(
        monkeypatch,
        [
            "5",
            "15",
        ],
    )

    def fake_update_expense_flow():
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "update_expense_flow",
        fake_update_expense_flow,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_budget_management(
    monkeypatch,
):
    captured = {"called": False}

    configure_cli_test(
        monkeypatch,
        [
            "7",
            "15",
        ],
    )

    def fake_manage_budgets():
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "manage_budgets",
        fake_manage_budgets,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_recommendation_management(
    monkeypatch,
):
    captured = {"called": False}

    configure_cli_test(
        monkeypatch,
        [
            "10",
            "15",
        ],
    )

    def fake_manage_recommendations():
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "manage_recommendations",
        fake_manage_recommendations,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_financial_trends(
    monkeypatch,
):
    captured: dict = {}

    configure_cli_test(
        monkeypatch,
        [
            "11",
            "15",
        ],
    )

    history = ["snapshot"]

    monkeypatch.setattr(
        cli,
        "get_history",
        lambda: history,
    )

    def fake_display_financial_trends(
        received_history,
    ):
        captured["history"] = received_history

    monkeypatch.setattr(
        cli,
        "display_financial_trends",
        fake_display_financial_trends,
    )

    cli.run_cli()

    assert captured["history"] == history


def test_run_cli_routes_forecast(
    monkeypatch,
):
    captured = {"called": False}

    configure_cli_test(
        monkeypatch,
        [
            "12",
            "15",
        ],
    )

    def fake_display_current_forecast():
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "display_current_forecast",
        fake_display_current_forecast,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_records_financial_snapshot(
    monkeypatch,
):
    captured: dict = {}

    configure_cli_test(
        monkeypatch,
        [
            "9",
            "15",
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
        received_snapshot,
    ):
        captured["snapshot"] = received_snapshot

    monkeypatch.setattr(
        cli,
        "display_financial_snapshot",
        fake_display_financial_snapshot,
    )

    cli.run_cli()

    assert captured["snapshot"] == snapshot


def test_run_cli_exits_with_option_14(
    monkeypatch,
    capsys,
):
    configure_cli_test(
        monkeypatch,
        [
            "15",
        ],
    )

    cli.run_cli()

    output = capsys.readouterr().out

    assert "Goodbye!" in output


def test_run_cli_rejects_invalid_option(
    monkeypatch,
    capsys,
):
    configure_cli_test(
        monkeypatch,
        [
            "invalid",
            "15",
        ],
    )

    cli.run_cli()

    output = capsys.readouterr().out

    assert "Invalid option." in output


def test_run_cli_routes_scenario_management(
    monkeypatch,
):
    captured = {"called": False}

    configure_cli_test(
        monkeypatch,
        [
            "13",
            "15",
        ],
    )

    def fake_manage_scenarios():
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "manage_scenarios",
        fake_manage_scenarios,
    )

    cli.run_cli()

    assert captured["called"] is True


def test_run_cli_routes_financial_coach(
    monkeypatch,
):
    captured = {
        "called": False,
    }

    configure_cli_test(
        monkeypatch,
        [
            "14",
            "15",
        ],
    )

    def fake_run_financial_coach():
        captured["called"] = True

    monkeypatch.setattr(
        cli,
        "run_financial_coach",
        fake_run_financial_coach,
    )

    cli.run_cli()

    assert captured["called"] is True
