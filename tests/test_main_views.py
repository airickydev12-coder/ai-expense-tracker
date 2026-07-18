"""Tests for the primary application menu view."""

from src.presentation.main_menu_view import (
    show_main_menu,
)


def test_show_main_menu(
    capsys,
) -> None:
    show_main_menu()

    output = capsys.readouterr().out

    expected_options = [
        "Financial Core",
        "1. Add Expense",
        "2. View Expenses",
        "3. View Total Spending",
        "4. Delete Expense",
        "5. Update Expense",
        "6. View Category Totals",
        "7. Manage Budgets",
        "8. View Budget Report",
        "9. View Financial Snapshot",
        "10. Manage Recommendations",
        "11. View Financial Trends",
        "12. View Financial Forecast",
        "13. Model Financial Scenarios",
        "14. AI Financial Coach",
        "15. Financial Goal Planner",
        "16. Exit",
    ]

    for expected_option in expected_options:
        assert expected_option in output


def test_show_main_menu_displays_options_in_order(
    capsys,
) -> None:
    show_main_menu()

    output = capsys.readouterr().out

    goal_planner_position = output.index("15. Financial Goal Planner")

    exit_position = output.index("16. Exit")

    assert goal_planner_position < exit_position
