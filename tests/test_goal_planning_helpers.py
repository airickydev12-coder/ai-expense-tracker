from collections.abc import Callable
from datetime import date
from decimal import Decimal

import pytest

from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal
from src.presentation.goal_planning_helpers import (
    confirm,
    pause,
    print_header,
    print_section,
    prompt_for_currency,
    prompt_for_date,
    prompt_for_float,
    prompt_for_goal_number,
    prompt_for_int,
    prompt_for_menu_choice,
    prompt_for_priority,
)


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


def make_input(
    responses: list[str],
) -> InputFunction:
    """Create an input function that returns responses in order."""
    iterator = iter(responses)

    def fake_input(
        prompt: str,
    ) -> str:
        del prompt
        return next(iterator)

    return fake_input


def collect_output() -> tuple[list[str], OutputFunction]:
    """Create an output collector and its output function."""
    messages: list[str] = []

    def fake_output(
        message: str,
    ) -> None:
        messages.append(message)

    return messages, fake_output


def build_goals() -> list[Goal]:
    """Create representative goals for selection tests."""
    return [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000"),
            current_amount=Decimal("4000"),
        ),
        Goal(
            id=2,
            name="Vacation",
            target_amount=Decimal("3000"),
            current_amount=Decimal("600"),
        ),
        Goal(
            id=3,
            name="Car Fund",
            target_amount=Decimal("12000"),
            current_amount=Decimal("4800"),
        ),
    ]


def test_prompt_for_int_returns_valid_integer():
    result = prompt_for_int(
        "Enter a number: ",
        input_fn=make_input(["25"]),
    )

    assert result == 25


def test_prompt_for_int_retries_after_invalid_input():
    messages, output_fn = collect_output()

    result = prompt_for_int(
        "Enter a number: ",
        input_fn=make_input(
            [
                "abc",
                "12",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == 12
    assert messages == ["Please enter a valid whole number."]


def test_prompt_for_int_enforces_minimum():
    messages, output_fn = collect_output()

    result = prompt_for_int(
        "Enter a number: ",
        minimum=5,
        input_fn=make_input(
            [
                "4",
                "5",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == 5
    assert messages == ["Please enter a value of at least 5."]


def test_prompt_for_int_enforces_maximum():
    messages, output_fn = collect_output()

    result = prompt_for_int(
        "Enter a number: ",
        maximum=10,
        input_fn=make_input(
            [
                "11",
                "10",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == 10
    assert messages == ["Please enter a value no greater than 10."]


def test_prompt_for_int_accepts_inclusive_range_boundaries():
    assert (
        prompt_for_int(
            "Enter a number: ",
            minimum=1,
            maximum=5,
            input_fn=make_input(["1"]),
        )
        == 1
    )

    assert (
        prompt_for_int(
            "Enter a number: ",
            minimum=1,
            maximum=5,
            input_fn=make_input(["5"]),
        )
        == 5
    )


def test_prompt_for_int_rejects_invalid_range():
    with pytest.raises(
        ValueError,
        match="Minimum",
    ):
        prompt_for_int(
            "Enter a number: ",
            minimum=10,
            maximum=5,
        )


def test_prompt_for_float_returns_valid_number():
    result = prompt_for_float(
        "Enter an amount: ",
        input_fn=make_input(["125.75"]),
    )

    assert result == 125.75


def test_prompt_for_float_accepts_currency_formatting():
    result = prompt_for_float(
        "Enter an amount: ",
        input_fn=make_input(["$1,250.50"]),
    )

    assert result == 1250.50


def test_prompt_for_float_retries_after_invalid_input():
    messages, output_fn = collect_output()

    result = prompt_for_float(
        "Enter an amount: ",
        input_fn=make_input(
            [
                "not-a-number",
                "49.95",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == 49.95
    assert messages == ["Please enter a valid number."]


def test_prompt_for_float_enforces_minimum_and_maximum():
    messages, output_fn = collect_output()

    result = prompt_for_float(
        "Enter an amount: ",
        minimum=10,
        maximum=20,
        input_fn=make_input(
            [
                "9",
                "21",
                "15.5",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == 15.5
    assert messages == [
        "Please enter a value of at least 10.",
        "Please enter a value no greater than 20.",
    ]


def test_prompt_for_float_rejects_invalid_range():
    with pytest.raises(
        ValueError,
        match="Minimum",
    ):
        prompt_for_float(
            "Enter an amount: ",
            minimum=100,
            maximum=50,
        )


def test_prompt_for_currency_returns_valid_amount():
    result = prompt_for_currency(
        "Enter monthly funding: ",
        input_fn=make_input(["$2,500.25"]),
    )

    assert result == 2500.25


def test_prompt_for_currency_rejects_negative_input():
    messages, output_fn = collect_output()

    result = prompt_for_currency(
        "Enter monthly funding: ",
        input_fn=make_input(
            [
                "-1",
                "0",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == 0
    assert messages == ["Please enter a value of at least 0."]


def test_prompt_for_currency_rejects_negative_minimum():
    with pytest.raises(
        ValueError,
        match="minimum",
    ):
        prompt_for_currency(
            "Enter monthly funding: ",
            minimum=-1,
        )


def test_prompt_for_currency_uses_custom_error_message():
    messages, output_fn = collect_output()

    result = prompt_for_currency(
        "Enter monthly funding: ",
        error_message="Invalid currency.",
        input_fn=make_input(
            [
                "bad",
                "100",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == 100
    assert messages == ["Invalid currency."]


def test_prompt_for_date_returns_valid_iso_date():
    result = prompt_for_date(
        "Enter target date: ",
        input_fn=make_input(["2027-07-18"]),
    )

    assert result == date(
        2027,
        7,
        18,
    )


def test_prompt_for_date_retries_after_invalid_format():
    messages, output_fn = collect_output()

    result = prompt_for_date(
        "Enter target date: ",
        input_fn=make_input(
            [
                "07/18/2027",
                "2027-07-18",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == date(
        2027,
        7,
        18,
    )

    assert messages == ["Please enter a valid date in YYYY-MM-DD format."]


def test_prompt_for_date_retries_after_impossible_date():
    messages, output_fn = collect_output()

    result = prompt_for_date(
        "Enter target date: ",
        input_fn=make_input(
            [
                "2027-02-30",
                "2027-02-28",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == date(
        2027,
        2,
        28,
    )

    assert messages == ["Please enter a valid date in YYYY-MM-DD format."]


def test_prompt_for_date_enforces_minimum():
    messages, output_fn = collect_output()

    result = prompt_for_date(
        "Enter target date: ",
        minimum=date(
            2027,
            1,
            1,
        ),
        input_fn=make_input(
            [
                "2026-12-31",
                "2027-01-01",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == date(
        2027,
        1,
        1,
    )

    assert messages == ["Please enter a date on or after 2027-01-01."]


def test_prompt_for_date_enforces_maximum():
    messages, output_fn = collect_output()

    result = prompt_for_date(
        "Enter target date: ",
        maximum=date(
            2027,
            12,
            31,
        ),
        input_fn=make_input(
            [
                "2028-01-01",
                "2027-12-31",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == date(
        2027,
        12,
        31,
    )

    assert messages == ["Please enter a date on or before 2027-12-31."]


def test_prompt_for_date_rejects_invalid_range():
    with pytest.raises(
        ValueError,
        match="Minimum date",
    ):
        prompt_for_date(
            "Enter target date: ",
            minimum=date(
                2028,
                1,
                1,
            ),
            maximum=date(
                2027,
                1,
                1,
            ),
        )


@pytest.mark.parametrize(
    (
        "selection",
        "expected_priority",
    ),
    [
        (
            "1",
            GoalPriority.LOW,
        ),
        (
            "2",
            GoalPriority.MEDIUM,
        ),
        (
            "3",
            GoalPriority.HIGH,
        ),
        (
            "4",
            GoalPriority.CRITICAL,
        ),
    ],
)
def test_prompt_for_priority_returns_selected_priority(
    selection: str,
    expected_priority: GoalPriority,
):
    messages, output_fn = collect_output()

    result = prompt_for_priority(
        input_fn=make_input([selection]),
        output_fn=output_fn,
    )

    assert result == expected_priority
    assert messages[:6] == [
        "Select Priority",
        "",
        "1. Low",
        "2. Medium",
        "3. High",
        "4. Critical",
    ]


def test_prompt_for_priority_retries_after_invalid_selection():
    messages, output_fn = collect_output()

    result = prompt_for_priority(
        input_fn=make_input(
            [
                "9",
                "3",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == GoalPriority.HIGH
    assert "Please enter a value no greater than 4." in messages


@pytest.mark.parametrize(
    "response",
    [
        "y",
        "Y",
        "yes",
        "YES",
        " Yes ",
    ],
)
def test_confirm_returns_true_for_affirmative_response(
    response: str,
):
    assert (
        confirm(
            "Continue? ",
            input_fn=make_input([response]),
        )
        is True
    )


@pytest.mark.parametrize(
    "response",
    [
        "n",
        "N",
        "no",
        "NO",
        "maybe",
        "anything",
    ],
)
def test_confirm_returns_false_for_nonaffirmative_response(
    response: str,
):
    assert (
        confirm(
            "Continue? ",
            input_fn=make_input([response]),
        )
        is False
    )


def test_confirm_returns_default_for_empty_input():
    assert (
        confirm(
            "Continue? ",
            default=True,
            input_fn=make_input([""]),
        )
        is True
    )

    assert (
        confirm(
            "Continue? ",
            default=False,
            input_fn=make_input(["   "]),
        )
        is False
    )


def test_prompt_for_menu_choice_returns_valid_choice():
    result = prompt_for_menu_choice(
        "Select option: ",
        minimum=1,
        maximum=6,
        input_fn=make_input(["4"]),
    )

    assert result == 4


def test_prompt_for_menu_choice_retries_until_valid():
    messages, output_fn = collect_output()

    result = prompt_for_menu_choice(
        "Select option: ",
        minimum=1,
        maximum=6,
        input_fn=make_input(
            [
                "abc",
                "0",
                "7",
                "2",
            ]
        ),
        output_fn=output_fn,
    )

    assert result == 2
    assert messages == [
        "Please enter a valid menu option.",
        "Please enter a value of at least 1.",
        "Please enter a value no greater than 6.",
    ]


def test_prompt_for_menu_choice_rejects_invalid_range():
    with pytest.raises(
        ValueError,
        match="Menu minimum",
    ):
        prompt_for_menu_choice(
            "Select option: ",
            minimum=6,
            maximum=1,
        )


def test_prompt_for_goal_number_returns_selected_goal():
    goals = build_goals()
    messages, output_fn = collect_output()

    result = prompt_for_goal_number(
        goals,
        input_fn=make_input(["2"]),
        output_fn=output_fn,
    )

    assert result is goals[1]
    assert result.name == "Vacation"

    assert messages == [
        "Available Goals",
        "",
        "1. Emergency Fund",
        "2. Vacation",
        "3. Car Fund",
    ]


def test_prompt_for_goal_number_retries_invalid_choice():
    goals = build_goals()
    messages, output_fn = collect_output()

    result = prompt_for_goal_number(
        goals,
        input_fn=make_input(
            [
                "0",
                "3",
            ]
        ),
        output_fn=output_fn,
    )

    assert result is goals[2]
    assert messages[-1] == ("Please enter a value of at least 1.")


def test_prompt_for_goal_number_rejects_empty_collection():
    with pytest.raises(
        ValueError,
        match="At least one goal",
    ):
        prompt_for_goal_number([])


def test_pause_uses_default_message():
    prompts: list[str] = []

    def fake_input(
        prompt: str,
    ) -> str:
        prompts.append(prompt)
        return ""

    result = pause(input_fn=fake_input)

    assert result is None
    assert prompts == ["Press Enter to continue..."]


def test_pause_uses_custom_message():
    prompts: list[str] = []

    def fake_input(
        prompt: str,
    ) -> str:
        prompts.append(prompt)
        return ""

    pause(
        "Continue when ready...",
        input_fn=fake_input,
    )

    assert prompts == ["Continue when ready..."]


def test_print_header():
    messages, output_fn = collect_output()

    print_header(
        "Financial Goal Planner",
        output_fn=output_fn,
    )

    assert messages == [
        "=" * 30,
        "Financial Goal Planner",
        "=" * 30,
    ]


def test_print_header_uses_custom_width():
    messages, output_fn = collect_output()

    print_header(
        "Planner",
        width=40,
        output_fn=output_fn,
    )

    assert messages == [
        "=" * 40,
        "Planner",
        "=" * 40,
    ]


def test_print_header_expands_width_for_long_title():
    messages, output_fn = collect_output()
    title = "A Financial Goal Planner With A Long Title"

    print_header(
        title,
        width=10,
        output_fn=output_fn,
    )

    assert messages == [
        "=" * len(title),
        title,
        "=" * len(title),
    ]


def test_print_header_normalizes_title():
    messages, output_fn = collect_output()

    print_header(
        "  Financial Goal Planner  ",
        output_fn=output_fn,
    )

    assert messages[1] == "Financial Goal Planner"


def test_print_header_rejects_empty_title():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        print_header("   ")


def test_print_header_rejects_invalid_width():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        print_header(
            "Planner",
            width=0,
        )


def test_print_section():
    messages, output_fn = collect_output()

    print_section(
        "Projection",
        output_fn=output_fn,
    )

    assert messages == [
        "-" * 10,
        "Projection",
        "-" * 10,
    ]


def test_print_section_uses_custom_width():
    messages, output_fn = collect_output()

    print_section(
        "Projection",
        width=20,
        output_fn=output_fn,
    )

    assert messages == [
        "-" * 20,
        "Projection",
        "-" * 20,
    ]


def test_print_section_expands_width_for_long_title():
    messages, output_fn = collect_output()
    title = "Monthly Funding Allocation"

    print_section(
        title,
        width=5,
        output_fn=output_fn,
    )

    assert messages == [
        "-" * len(title),
        title,
        "-" * len(title),
    ]


def test_print_section_rejects_empty_title():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        print_section(" ")


def test_print_section_rejects_invalid_width():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        print_section(
            "Projection",
            width=-1,
        )
