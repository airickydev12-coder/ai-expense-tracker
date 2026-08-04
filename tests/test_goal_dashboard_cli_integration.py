"""Integration tests for the goal dashboard in the planner CLI."""

from datetime import date
from decimal import Decimal

import pytest

from src.financial.goals.models import Goal
from src.presentation import goal_planning_cli


def test_run_goal_planning_menu_displays_dashboard(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("4000.00"),
    )
    expected_dashboard = object()
    captured: dict[str, object] = {}
    messages: list[str] = []

    monkeypatch.setattr(
        goal_planning_cli,
        "build_goal_dashboard",
        lambda goals, **kwargs: (
            captured.update(
                goals=goals,
                requests=kwargs["requests_by_goal_id"],
                as_of_date=kwargs["as_of_date"],
            )
            or expected_dashboard
        ),
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_dashboard",
        lambda dashboard: (
            "Rendered dashboard"
            if dashboard is expected_dashboard
            else "Wrong dashboard"
        ),
    )

    goal_planning_cli.run_goal_planning_menu(
        1,
        [goal],
        input_fn=lambda prompt: "7",
        output_fn=messages.append,
        today=date(2027, 1, 1),
        planning_file_path=tmp_path / "planning.db",
    )

    assert captured["goals"] == [goal]
    assert captured["requests"] == {}
    assert captured["as_of_date"] == date(2027, 1, 1)
    assert "Rendered dashboard" in messages
