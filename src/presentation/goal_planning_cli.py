"""Interactive command-line controller for financial goal planning."""

from collections.abc import Callable, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from src.core.config import DB_PATH
from src.core.exceptions import ValidationError
from src.core.money import CURRENCY_PRECISION
from src.financial.application.goal_dashboard_service import (
    build_goal_dashboard,
)
from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
    GoalPlanningResult,
    MoneyInput,
    analyze_goals,
)
from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal
from src.financial.planning.repository import (
    load_goal_planning_requests_from_file,
    save_goal_planning_requests_to_file,
)
from src.presentation.goal_dashboard_views import (
    render_goal_dashboard,
)
from src.presentation.goal_planning_helpers import (
    pause,
    print_header,
    print_section,
    prompt_for_currency,
    prompt_for_date,
    prompt_for_goal_number,
    prompt_for_menu_choice,
    prompt_for_priority,
)
from src.presentation.goal_planning_views import (
    render_goal_planning_request,
    render_goal_planning_request_list,
    render_goal_planning_result,
)

InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]

GOAL_PLANNING_MENU_MINIMUM = 1
GOAL_PLANNING_MENU_MAXIMUM = 7


def run_goal_planning_menu(
    user_id: int,
    goals: Sequence[Goal],
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
    today: date | None = None,
    planning_file_path: Path = DB_PATH,
) -> None:
    """
    Run the interactive Financial Goal Planner menu.

    Planning requests are loaded from and saved to persistent JSON storage.
    The underlying Goal objects are not modified.
    """
    planning_date = today or date.today()
    requests_by_goal_id = load_goal_planning_requests_from_file(
        user_id,
        goals,
        file_path=planning_file_path,
    )

    save_goal_planning_requests_to_file(
        requests_by_goal_id,
        user_id,
        file_path=planning_file_path,
    )

    while True:
        dashboard = build_goal_dashboard(
            goals,
            requests_by_goal_id=requests_by_goal_id,
            as_of_date=planning_date,
        )

        output_fn("")
        output_fn(render_goal_dashboard(dashboard))
        output_fn("")

        display_goal_planning_menu(
            output_fn=output_fn,
        )

        choice = prompt_for_menu_choice(
            "Select an option: ",
            minimum=GOAL_PLANNING_MENU_MINIMUM,
            maximum=GOAL_PLANNING_MENU_MAXIMUM,
            input_fn=input_fn,
            output_fn=output_fn,
        )

        if choice == 1:
            analyze_all_goals_workflow(
                goals,
                requests_by_goal_id=requests_by_goal_id,
                today=planning_date,
                input_fn=input_fn,
                output_fn=output_fn,
            )
            save_goal_planning_requests_to_file(
                requests_by_goal_id,
                user_id,
                file_path=planning_file_path,
            )
        elif choice == 2:
            analyze_single_goal_workflow(
                goals,
                requests_by_goal_id=requests_by_goal_id,
                today=planning_date,
                input_fn=input_fn,
                output_fn=output_fn,
            )
            save_goal_planning_requests_to_file(
                requests_by_goal_id,
                user_id,
                file_path=planning_file_path,
            )
        elif choice == 3:
            monthly_allocation_workflow(
                goals,
                requests_by_goal_id=requests_by_goal_id,
                today=planning_date,
                input_fn=input_fn,
                output_fn=output_fn,
            )
            save_goal_planning_requests_to_file(
                requests_by_goal_id,
                user_id,
                file_path=planning_file_path,
            )
        elif choice == 4:
            view_planning_requests_workflow(
                requests_by_goal_id,
                input_fn=input_fn,
                output_fn=output_fn,
            )
        elif choice == 5:
            update_planning_request_workflow(
                requests_by_goal_id,
                today=planning_date,
                input_fn=input_fn,
                output_fn=output_fn,
            )
            save_goal_planning_requests_to_file(
                requests_by_goal_id,
                user_id,
                file_path=planning_file_path,
            )
        elif choice == 6:
            delete_planning_request_workflow(
                requests_by_goal_id,
                input_fn=input_fn,
                output_fn=output_fn,
            )
            save_goal_planning_requests_to_file(
                requests_by_goal_id,
                user_id,
                file_path=planning_file_path,
            )
        else:
            output_fn("Returning to the main menu.")
            return


def display_goal_planning_menu(
    *,
    output_fn: OutputFunction = print,
) -> None:
    """Display the Financial Goal Planner menu."""
    print_header(
        "Financial Goal Planner",
        output_fn=output_fn,
    )

    output_fn("1. Analyze All Goals")
    output_fn("2. Analyze One Goal")
    output_fn("3. Monthly Allocation Planner")
    output_fn("4. View Planning Requests")
    output_fn("5. Update Planning Request")
    output_fn("6. Delete Planning Request")
    output_fn("7. Return to Main Menu")


def analyze_all_goals_workflow(
    goals: Sequence[Goal],
    *,
    requests_by_goal_id: dict[int, GoalPlanningRequest],
    today: date,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> GoalPlanningResult | None:
    """
    Collect planning information for every goal and analyze the full plan.

    Existing requests for a goal are replaced with the newly collected
    request.
    """
    print_section(
        "Analyze All Goals",
        output_fn=output_fn,
    )

    if not _ensure_goals_exist(
        goals,
        output_fn=output_fn,
    ):
        pause(
            input_fn=input_fn,
        )
        return None

    requests: list[GoalPlanningRequest] = []

    for goal in goals:
        output_fn("")
        request = build_goal_planning_request(
            goal,
            today=today,
            input_fn=input_fn,
            output_fn=output_fn,
        )

        requests.append(request)
        requests_by_goal_id[goal.id] = request

    total_available = collect_monthly_budget(
        input_fn=input_fn,
        output_fn=output_fn,
    )

    result = analyze_planning_requests(
        requests,
        total_available=total_available,
        as_of_date=today,
    )

    output_fn("")
    output_fn(render_goal_planning_result(result))

    pause(
        input_fn=input_fn,
    )

    return result


def analyze_single_goal_workflow(
    goals: Sequence[Goal],
    *,
    requests_by_goal_id: dict[int, GoalPlanningRequest],
    today: date,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> GoalPlanningResult | None:
    """Collect planning information for one goal and analyze it."""
    print_section(
        "Analyze One Goal",
        output_fn=output_fn,
    )

    if not _ensure_goals_exist(
        goals,
        output_fn=output_fn,
    ):
        pause(
            input_fn=input_fn,
        )
        return None

    goal = prompt_for_goal_number(
        goals,
        input_fn=input_fn,
        output_fn=output_fn,
    )

    request = build_goal_planning_request(
        goal,
        today=today,
        input_fn=input_fn,
        output_fn=output_fn,
    )

    requests_by_goal_id[goal.id] = request

    total_available = collect_monthly_budget(
        input_fn=input_fn,
        output_fn=output_fn,
    )

    result = analyze_planning_requests(
        [request],
        total_available=total_available,
        as_of_date=today,
    )

    output_fn("")
    output_fn(render_goal_planning_result(result))

    pause(
        input_fn=input_fn,
    )

    return result


def monthly_allocation_workflow(
    goals: Sequence[Goal],
    *,
    requests_by_goal_id: dict[int, GoalPlanningRequest],
    today: date,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> GoalPlanningResult | None:
    """
    Build or reuse planning requests and allocate available monthly funding.

    Missing goal requests are collected before the allocation analysis runs.
    """
    print_section(
        "Monthly Allocation Planner",
        output_fn=output_fn,
    )

    if not _ensure_goals_exist(
        goals,
        output_fn=output_fn,
    ):
        pause(
            input_fn=input_fn,
        )
        return None

    requests = collect_missing_planning_requests(
        goals,
        requests_by_goal_id=requests_by_goal_id,
        today=today,
        input_fn=input_fn,
        output_fn=output_fn,
    )

    total_available = collect_monthly_budget(
        input_fn=input_fn,
        output_fn=output_fn,
    )

    result = analyze_planning_requests(
        requests,
        total_available=total_available,
        as_of_date=today,
    )

    output_fn("")
    output_fn(render_goal_planning_result(result))

    pause(
        input_fn=input_fn,
    )

    return result


def view_planning_requests_workflow(
    requests_by_goal_id: dict[int, GoalPlanningRequest],
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> None:
    """Display all persisted planning requests."""
    print_section(
        "Planning Requests",
        output_fn=output_fn,
    )

    requests = list(requests_by_goal_id.values())

    if not requests:
        output_fn("No planning requests have been saved yet.")
    else:
        output_fn(render_goal_planning_request_list(requests))

    pause(
        input_fn=input_fn,
    )


def update_planning_request_workflow(
    requests_by_goal_id: dict[int, GoalPlanningRequest],
    *,
    today: date,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> GoalPlanningRequest | None:
    """Update one saved planning request while preserving blank fields."""
    print_section(
        "Update Planning Request",
        output_fn=output_fn,
    )

    requests = list(requests_by_goal_id.values())

    if not requests:
        output_fn("No planning requests have been saved yet.")
        pause(input_fn=input_fn)
        return None

    output_fn(render_goal_planning_request_list(requests))
    output_fn("")

    selection = prompt_for_menu_choice(
        "Select a planning request to update: ",
        minimum=1,
        maximum=len(requests),
        input_fn=input_fn,
        output_fn=output_fn,
    )
    current_request = requests[selection - 1]

    output_fn("")
    output_fn(render_goal_planning_request(current_request))
    output_fn("")
    output_fn("Press Enter to keep the current value.")

    target_date = _prompt_for_updated_date(
        current_request.target_date,
        minimum=today,
        input_fn=input_fn,
        output_fn=output_fn,
    )
    monthly_contribution = _prompt_for_updated_currency(
        current_request.planned_monthly_contribution,
        input_fn=input_fn,
        output_fn=output_fn,
    )
    priority = _prompt_for_updated_priority(
        current_request.priority,
        input_fn=input_fn,
        output_fn=output_fn,
    )

    updated_request = GoalPlanningRequest(
        goal=current_request.goal,
        target_date=target_date,
        planned_monthly_contribution=monthly_contribution,
        priority=priority,
    )
    requests_by_goal_id[current_request.goal.id] = updated_request

    output_fn("")
    output_fn("Planning request updated successfully.")
    output_fn(render_goal_planning_request(updated_request))

    pause(input_fn=input_fn)
    return updated_request


def delete_planning_request_workflow(
    requests_by_goal_id: dict[int, GoalPlanningRequest],
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> GoalPlanningRequest | None:
    """Delete one saved planning request after user confirmation."""
    print_section(
        "Delete Planning Request",
        output_fn=output_fn,
    )

    requests = list(requests_by_goal_id.values())

    if not requests:
        output_fn("No planning requests have been saved yet.")
        pause(input_fn=input_fn)
        return None

    output_fn(render_goal_planning_request_list(requests))
    output_fn("")

    selection = prompt_for_menu_choice(
        "Select a planning request to delete: ",
        minimum=1,
        maximum=len(requests),
        input_fn=input_fn,
        output_fn=output_fn,
    )
    selected_request = requests[selection - 1]

    while True:
        confirmation = (
            input_fn(
                f'Delete planning request for "{selected_request.goal.name}"? (Y/N): '
            )
            .strip()
            .upper()
        )

        if confirmation in {"Y", "YES"}:
            del requests_by_goal_id[selected_request.goal.id]
            output_fn("")
            output_fn("Planning request deleted successfully.")
            pause(input_fn=input_fn)
            return selected_request

        if confirmation in {"N", "NO"}:
            output_fn("")
            output_fn("Deletion cancelled.")
            pause(input_fn=input_fn)
            return None

        output_fn("Enter Y to confirm or N to cancel.")


def _prompt_for_updated_date(
    current_value: date,
    *,
    minimum: date,
    input_fn: InputFunction,
    output_fn: OutputFunction,
) -> date:
    """Prompt for an optional replacement date."""
    while True:
        raw_value = input_fn(
            f"Target date [{current_value.isoformat()}] (YYYY-MM-DD): "
        ).strip()

        if not raw_value:
            return current_value

        try:
            updated_value = date.fromisoformat(raw_value)
        except ValueError:
            output_fn("Enter a valid date in YYYY-MM-DD format.")
            continue

        if updated_value < minimum:
            output_fn(f"Date must be on or after {minimum.isoformat()}.")
            continue

        return updated_value


def _prompt_for_updated_currency(
    current_value: MoneyInput,
    *,
    input_fn: InputFunction,
    output_fn: OutputFunction,
) -> Decimal:
    """Prompt for an optional nonnegative monetary replacement."""
    try:
        current_amount = Decimal(str(current_value)).quantize(CURRENCY_PRECISION)
    except (InvalidOperation, ValueError) as error:
        raise ValidationError(
            "current_value must be a valid monetary amount."
        ) from error

    if not current_amount.is_finite():
        raise ValidationError("current_value must be a finite monetary amount.")

    if current_amount < 0:
        raise ValidationError("current_value cannot be negative.")

    while True:
        raw_value = input_fn(
            f"Monthly contribution [${current_amount:,.2f}]: $"
        ).strip()

        if not raw_value:
            return current_amount

        try:
            updated_value = Decimal(raw_value.replace(",", "")).quantize(
                CURRENCY_PRECISION
            )
        except InvalidOperation:
            output_fn("Enter a valid monetary amount.")
            continue

        if not updated_value.is_finite():
            output_fn("Enter a finite monetary amount.")
            continue

        if updated_value < 0:
            output_fn("Monetary amount cannot be negative.")
            continue

        return updated_value


def _prompt_for_updated_priority(
    current_value: GoalPriority,
    *,
    input_fn: InputFunction,
    output_fn: OutputFunction,
) -> GoalPriority:
    """Prompt for an optional replacement goal priority."""
    priorities = list(GoalPriority)
    choices = ", ".join(priority.name for priority in priorities)

    while True:
        raw_value = input_fn(f"Priority [{current_value.name}] ({choices}): ").strip()

        if not raw_value:
            return current_value

        normalized = raw_value.upper().replace(" ", "_")
        priority = GoalPriority.__members__.get(normalized)

        if priority is not None:
            return priority

        if raw_value.isdigit():
            index = int(raw_value) - 1
            if 0 <= index < len(priorities):
                return priorities[index]

        output_fn("Enter a valid priority name or its menu number.")


def build_goal_planning_request(
    goal: Goal,
    *,
    today: date,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> GoalPlanningRequest:
    """Collect the planning inputs required for one financial goal."""
    if not isinstance(goal, Goal):
        raise TypeError("goal must be a Goal instance.")

    if not isinstance(today, date):
        raise TypeError("today must be a date instance.")

    print_section(
        goal.name,
        output_fn=output_fn,
    )

    output_fn(f"Target amount: ${goal.target_amount:,.2f}")
    output_fn(f"Current amount: ${goal.current_amount:,.2f}")

    target_date = prompt_for_date(
        "Enter target date (YYYY-MM-DD): ",
        minimum=today,
        input_fn=input_fn,
        output_fn=output_fn,
    )

    planned_monthly_contribution = prompt_for_currency(
        "Enter planned monthly contribution: $",
        input_fn=input_fn,
        output_fn=output_fn,
    )

    priority = prompt_for_priority(
        input_fn=input_fn,
        output_fn=output_fn,
    )

    request = GoalPlanningRequest(
        goal=goal,
        target_date=target_date,
        planned_monthly_contribution=planned_monthly_contribution,
        priority=priority,
    )

    output_fn("")
    output_fn(render_goal_planning_request(request))

    return request


def collect_missing_planning_requests(
    goals: Sequence[Goal],
    *,
    requests_by_goal_id: dict[int, GoalPlanningRequest],
    today: date,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> list[GoalPlanningRequest]:
    """
    Return one planning request per goal.

    Existing requests are reused. Requests are collected only for goals that
    do not already have a persisted request.
    """
    requests: list[GoalPlanningRequest] = []

    for goal in goals:
        existing_request = requests_by_goal_id.get(goal.id)

        if existing_request is not None:
            requests.append(existing_request)
            continue

        output_fn("")
        output_fn(f"No planning request exists for {goal.name}.")

        request = build_goal_planning_request(
            goal,
            today=today,
            input_fn=input_fn,
            output_fn=output_fn,
        )

        requests_by_goal_id[goal.id] = request
        requests.append(request)

    return requests


def collect_monthly_budget(
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> Decimal:
    """Collect the total amount available for monthly goal funding."""
    output_fn("")

    value = prompt_for_currency(
        "Enter total monthly funding available: $",
        input_fn=input_fn,
        output_fn=output_fn,
    )

    return Decimal(str(value)).quantize(CURRENCY_PRECISION)


def analyze_planning_requests(
    requests: Sequence[GoalPlanningRequest],
    *,
    total_available: Decimal,
    as_of_date: date | None = None,
) -> GoalPlanningResult:
    """Validate and analyze a collection of goal-planning requests."""
    if not requests:
        raise ValidationError("At least one planning request is required.")

    if total_available < 0:
        raise ValidationError("Total available funding cannot be negative.")

    return analyze_goals(
        list(requests),
        total_available=total_available,
        as_of_date=as_of_date,
    )


def _ensure_goals_exist(
    goals: Sequence[Goal],
    *,
    output_fn: OutputFunction,
) -> bool:
    """Report whether the CLI has at least one goal to process."""
    if goals:
        return True

    output_fn("No financial goals are available.")
    output_fn("Create at least one goal before using the planner.")

    return False
