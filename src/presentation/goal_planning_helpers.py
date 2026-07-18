"""Reusable input and display helpers for the goal-planning CLI."""

from collections.abc import Callable, Sequence
from datetime import date

from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


def prompt_for_int(
    prompt: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
    error_message: str = "Please enter a valid whole number.",
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> int:
    """
    Prompt repeatedly until the user enters a valid integer.

    Optional minimum and maximum values are inclusive.
    """
    _validate_numeric_range(
        minimum=minimum,
        maximum=maximum,
    )

    while True:
        raw_value = input_fn(prompt).strip()

        try:
            value = int(raw_value)
        except ValueError:
            output_fn(error_message)
            continue

        if minimum is not None and value < minimum:
            output_fn(f"Please enter a value of at least {minimum}.")
            continue

        if maximum is not None and value > maximum:
            output_fn(f"Please enter a value no greater than {maximum}.")
            continue

        return value


def prompt_for_float(
    prompt: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    error_message: str = "Please enter a valid number.",
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> float:
    """
    Prompt repeatedly until the user enters a valid floating-point value.

    Commas and a leading dollar sign are accepted, allowing values such as
    "$1,250.50". Optional minimum and maximum values are inclusive.
    """
    _validate_numeric_range(
        minimum=minimum,
        maximum=maximum,
    )

    while True:
        raw_value = input_fn(prompt).strip()
        normalized_value = _normalize_numeric_input(raw_value)

        try:
            value = float(normalized_value)
        except ValueError:
            output_fn(error_message)
            continue

        if minimum is not None and value < minimum:
            output_fn(
                f"Please enter a value of at least " f"{_format_number(minimum)}."
            )
            continue

        if maximum is not None and value > maximum:
            output_fn(
                f"Please enter a value no greater than " f"{_format_number(maximum)}."
            )
            continue

        return value


def prompt_for_currency(
    prompt: str,
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
    error_message: str = "Please enter a valid monetary amount.",
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> float:
    """
    Prompt for a nonnegative currency amount.

    A custom minimum may be supplied, but it cannot be negative.
    """
    if minimum < 0:
        raise ValueError("Currency minimum cannot be negative.")

    return prompt_for_float(
        prompt,
        minimum=minimum,
        maximum=maximum,
        error_message=error_message,
        input_fn=input_fn,
        output_fn=output_fn,
    )


def prompt_for_date(
    prompt: str,
    *,
    minimum: date | None = None,
    maximum: date | None = None,
    error_message: str = ("Please enter a valid date in YYYY-MM-DD format."),
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> date:
    """
    Prompt repeatedly for a date in ISO YYYY-MM-DD format.

    Optional minimum and maximum dates are inclusive.
    """
    _validate_date_range(
        minimum=minimum,
        maximum=maximum,
    )

    while True:
        raw_value = input_fn(prompt).strip()

        try:
            value = date.fromisoformat(raw_value)
        except ValueError:
            output_fn(error_message)
            continue

        if minimum is not None and value < minimum:
            output_fn("Please enter a date on or after " f"{minimum.isoformat()}.")
            continue

        if maximum is not None and value > maximum:
            output_fn("Please enter a date on or before " f"{maximum.isoformat()}.")
            continue

        return value


def prompt_for_priority(
    prompt: str = "Select priority: ",
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> GoalPriority:
    """Display the priority menu and return the selected priority."""
    output_fn("Select Priority")
    output_fn("")
    output_fn("1. Low")
    output_fn("2. Medium")
    output_fn("3. High")
    output_fn("4. Critical")

    selection = prompt_for_menu_choice(
        prompt,
        minimum=1,
        maximum=4,
        input_fn=input_fn,
        output_fn=output_fn,
    )

    priorities = {
        1: GoalPriority.LOW,
        2: GoalPriority.MEDIUM,
        3: GoalPriority.HIGH,
        4: GoalPriority.CRITICAL,
    }

    return priorities[selection]


def confirm(
    prompt: str,
    *,
    default: bool = False,
    input_fn: InputFunction = input,
) -> bool:
    """
    Ask the user for confirmation.

    Accepted affirmative values are "y" and "yes". Accepted negative values
    are "n" and "no". Empty input returns the supplied default value. Any
    other response returns False.
    """
    response = input_fn(prompt).strip().lower()

    if not response:
        return default

    return response in {
        "y",
        "yes",
    }


def prompt_for_menu_choice(
    prompt: str,
    *,
    minimum: int,
    maximum: int,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> int:
    """Prompt for an integer menu selection within an inclusive range."""
    if minimum > maximum:
        raise ValueError("Menu minimum cannot be greater than menu maximum.")

    return prompt_for_int(
        prompt,
        minimum=minimum,
        maximum=maximum,
        error_message="Please enter a valid menu option.",
        input_fn=input_fn,
        output_fn=output_fn,
    )


def prompt_for_goal_number(
    goals: Sequence[Goal],
    prompt: str = "Select a goal: ",
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> Goal:
    """Display available goals and return the selected goal."""
    if not goals:
        raise ValueError("At least one goal is required for selection.")

    output_fn("Available Goals")
    output_fn("")

    for index, goal in enumerate(
        goals,
        start=1,
    ):
        output_fn(f"{index}. {goal.name}")

    selection = prompt_for_menu_choice(
        prompt,
        minimum=1,
        maximum=len(goals),
        input_fn=input_fn,
        output_fn=output_fn,
    )

    return goals[selection - 1]


def pause(
    message: str = "Press Enter to continue...",
    *,
    input_fn: InputFunction = input,
) -> None:
    """Pause CLI execution until the user presses Enter."""
    input_fn(message)


def print_header(
    title: str,
    *,
    width: int | None = None,
    output_fn: OutputFunction = print,
) -> None:
    """Print a prominent CLI header."""
    normalized_title = title.strip()

    if not normalized_title:
        raise ValueError("Header title cannot be empty.")

    separator_width = _resolve_separator_width(
        title=normalized_title,
        width=width,
        minimum_width=30,
    )

    separator = "=" * separator_width

    output_fn(separator)
    output_fn(normalized_title)
    output_fn(separator)


def print_section(
    title: str,
    *,
    width: int | None = None,
    output_fn: OutputFunction = print,
) -> None:
    """Print a secondary CLI section heading."""
    normalized_title = title.strip()

    if not normalized_title:
        raise ValueError("Section title cannot be empty.")

    separator_width = _resolve_separator_width(
        title=normalized_title,
        width=width,
        minimum_width=10,
    )

    separator = "-" * separator_width

    output_fn(separator)
    output_fn(normalized_title)
    output_fn(separator)


def _normalize_numeric_input(
    raw_value: str,
) -> str:
    """Remove supported currency formatting from numeric input."""
    normalized_value = raw_value.replace(
        ",",
        "",
    )

    if normalized_value.startswith("$"):
        normalized_value = normalized_value[1:].strip()

    return normalized_value


def _validate_numeric_range(
    *,
    minimum: int | float | None,
    maximum: int | float | None,
) -> None:
    """Validate optional numeric boundaries."""
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("Minimum cannot be greater than maximum.")


def _validate_date_range(
    *,
    minimum: date | None,
    maximum: date | None,
) -> None:
    """Validate optional date boundaries."""
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("Minimum date cannot be greater than maximum date.")


def _resolve_separator_width(
    *,
    title: str,
    width: int | None,
    minimum_width: int,
) -> int:
    """Return a validated separator width for a heading."""
    if width is not None and width <= 0:
        raise ValueError("Heading width must be greater than zero.")

    if width is None:
        return max(
            len(title),
            minimum_width,
        )

    return max(
        width,
        len(title),
    )


def _format_number(
    value: int | float,
) -> str:
    """Format numeric range boundaries for validation messages."""
    numeric_value = float(value)

    if numeric_value.is_integer():
        return str(int(numeric_value))

    return str(value)
