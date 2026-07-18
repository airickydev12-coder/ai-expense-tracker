"""Interactive command-line controller for financial goal planning."""

from collections.abc import Callable, Sequence
from datetime import date

from src.financial.application.goal_dashboard_service import (
    build_goal_dashboard,
)
from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
    GoalPlanningResult,
    analyze_goals,
)
from src.financial.goals.models import Goal
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
from src.presentation.goal_dashboard_views import (
    render_goal_dashboard,
)
from src.presentation.goal_planning_views import (
    render_goal_planning_request,
    render_goal_planning_request_list,
    render_goal_planning_result,
)


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]

GOAL_PLANNING_MENU_MINIMUM = 1
GOAL_PLANNING_MENU_MAXIMUM = 5


def run_goal_planning_menu(
    goals: Sequence[Goal],
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
    today: date | None = None,
) -> None:
    """
    Run the interactive Financial Goal Planner menu.

    Planning requests are retained only for the duration of the current menu
    session. The underlying Goal objects are not modified.
    """
    planning_date = today or date.today()
    requests_by_goal_id: dict[int, GoalPlanningRequest] = {}

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
        elif choice == 2:
            analyze_single_goal_workflow(
                goals,
                requests_by_goal_id=requests_by_goal_id,
                today=planning_date,
                input_fn=input_fn,
                output_fn=output_fn,
            )
        elif choice == 3:
            monthly_allocation_workflow(
                goals,
                requests_by_goal_id=requests_by_goal_id,
                today=planning_date,
                input_fn=input_fn,
                output_fn=output_fn,
            )
        elif choice == 4:
            view_planning_requests_workflow(
                requests_by_goal_id,
                input_fn=input_fn,
                output_fn=output_fn,
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
    output_fn("5. Return to Main Menu")


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
    """Display all planning requests created during the current session."""
    print_section(
        "Planning Requests",
        output_fn=output_fn,
    )

    requests = list(requests_by_goal_id.values())

    if not requests:
        output_fn("No planning requests have been created yet.")
    else:
        output_fn(render_goal_planning_request_list(requests))

    pause(
        input_fn=input_fn,
    )


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
    do not already have one in the current session.
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
) -> float:
    """Collect the total amount available for monthly goal funding."""
    output_fn("")

    return prompt_for_currency(
        "Enter total monthly funding available: $",
        input_fn=input_fn,
        output_fn=output_fn,
    )


def analyze_planning_requests(
    requests: Sequence[GoalPlanningRequest],
    *,
    total_available: float,
    as_of_date: date | None = None,
) -> GoalPlanningResult:
    """Validate and analyze a collection of goal-planning requests."""
    if not requests:
        raise ValueError("At least one planning request is required.")

    if total_available < 0:
        raise ValueError("Total available funding cannot be negative.")

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
