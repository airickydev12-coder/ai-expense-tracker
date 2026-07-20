from datetime import date
from decimal import Decimal

from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
    analyze_goals,
)
from src.financial.goals.allocation import (
    GoalAllocation,
    GoalAllocationPlan,
    GoalPriority,
)
from src.financial.goals.feasibility import assess_goal_feasibility
from src.financial.goals.models import Goal
from src.financial.goals.projections import build_goal_projection
from src.presentation.goal_planning_views import (
    format_boolean,
    format_currency,
    format_date,
    format_priority,
    render_goal_allocation,
    render_goal_allocation_plan,
    render_goal_feasibility_assessment,
    render_goal_funding_gap_report,
    render_goal_planning_request,
    render_goal_planning_request_list,
    render_goal_planning_result,
    render_goal_planning_summary,
    render_goal_priority_report,
    render_goal_projection,
)


AS_OF_DATE = date(
    2026,
    7,
    18,
)


def build_request(
    *,
    goal_id: int = 1,
    name: str = "Emergency Fund",
    target_amount: Decimal = Decimal("10000.00"),
    current_amount: Decimal = Decimal("4000.00"),
    target_date: date = date(
        2027,
        7,
        18,
    ),
    planned_monthly_contribution: Decimal = Decimal("500.00"),
    priority: GoalPriority = GoalPriority.HIGH,
) -> GoalPlanningRequest:
    """Build a valid request for view tests."""
    return GoalPlanningRequest(
        goal=Goal(
            id=goal_id,
            name=name,
            target_amount=target_amount,
            current_amount=current_amount,
        ),
        target_date=target_date,
        planned_monthly_contribution=planned_monthly_contribution,
        priority=priority,
    )


def build_standard_requests() -> list[GoalPlanningRequest]:
    """Build representative goal-planning requests."""
    return [
        build_request(
            goal_id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("4000.00"),
            target_date=date(
                2027,
                7,
                18,
            ),
            planned_monthly_contribution=Decimal("500.00"),
            priority=GoalPriority.CRITICAL,
        ),
        build_request(
            goal_id=2,
            name="Vacation",
            target_amount=Decimal("3000.00"),
            current_amount=Decimal("600.00"),
            target_date=date(
                2027,
                3,
                18,
            ),
            planned_monthly_contribution=Decimal("200.00"),
            priority=GoalPriority.LOW,
        ),
        build_request(
            goal_id=3,
            name="Car Fund",
            target_amount=Decimal("12000.00"),
            current_amount=Decimal("4800.00"),
            target_date=date(
                2027,
                7,
                18,
            ),
            planned_monthly_contribution=Decimal("0.00"),
            priority=GoalPriority.HIGH,
        ),
    ]


def build_result(
    *,
    total_available: Decimal = Decimal("1000.00"),
):
    """Build a complete result for view tests."""
    return analyze_goals(
        build_standard_requests(),
        total_available=total_available,
        as_of_date=AS_OF_DATE,
    )


def test_format_currency():
    assert format_currency(Decimal("1250.00")) == "$1,250.00"
    assert format_currency(Decimal("0.00")) == "$0.00"
    assert format_currency(Decimal("12.50")) == "$12.50"


def test_format_date():
    assert format_date(date(2027, 7, 18)) == "July 18, 2027"
    assert format_date(None) == "Not projected"


def test_format_priority():
    assert format_priority(GoalPriority.CRITICAL) == "Critical"
    assert format_priority(GoalPriority.MEDIUM) == "Medium"


def test_format_boolean():
    assert format_boolean(True) == "Yes"
    assert format_boolean(False) == "No"


def test_render_goal_planning_request():
    output = render_goal_planning_request(build_request())

    assert "Goal: Emergency Fund" in output
    assert "Goal ID: 1" in output
    assert "Current Amount: $4,000.00" in output
    assert "Target Amount: $10,000.00" in output
    assert "Target Date: July 18, 2027" in output
    assert "Planned Monthly Contribution: $500.00" in output
    assert "Priority: High" in output


def test_render_goal_projection():
    request = build_request()

    projection = build_goal_projection(
        request.goal,
        target_date=request.target_date,
        planned_monthly_contribution=request.planned_monthly_contribution,
        as_of_date=AS_OF_DATE,
    )

    output = render_goal_projection(projection)

    assert "Goal: Emergency Fund" in output
    assert "Remaining Amount: $6,000.00" in output
    assert "Months Remaining: 12" in output
    assert "Required Monthly Contribution: $500.00" in output
    assert "Planned Monthly Contribution: $500.00" in output
    assert "Monthly Contribution Surplus: $0.00" in output
    assert "Projected Completion Date: July 18, 2027" in output
    assert "Goal Complete: No" in output
    assert "Deadline Passed: No" in output


def test_render_projection_with_shortfall():
    request = build_request(
        planned_monthly_contribution=Decimal("300.00"),
    )

    projection = build_goal_projection(
        request.goal,
        target_date=request.target_date,
        planned_monthly_contribution=request.planned_monthly_contribution,
        as_of_date=AS_OF_DATE,
    )

    output = render_goal_projection(projection)

    assert "Monthly Contribution Shortfall: $200.00" in output


def test_render_projection_without_completion_date():
    request = build_request(
        planned_monthly_contribution=Decimal("0.00"),
    )

    projection = build_goal_projection(
        request.goal,
        target_date=request.target_date,
        planned_monthly_contribution=Decimal("0.00"),
        as_of_date=AS_OF_DATE,
    )

    output = render_goal_projection(projection)

    assert "Projected Completion Date: Not projected" in output


def test_render_goal_feasibility_assessment():
    request = build_request()

    projection = build_goal_projection(
        request.goal,
        target_date=request.target_date,
        planned_monthly_contribution=request.planned_monthly_contribution,
        as_of_date=AS_OF_DATE,
    )

    assessment = assess_goal_feasibility(projection)
    output = render_goal_feasibility_assessment(assessment)

    assert "Goal: Emergency Fund" in output
    assert "Status: Feasible" in output
    assert "Feasible: Yes" in output
    assert "Remaining Amount: $6,000.00" in output
    assert "Months Remaining: 12" in output
    assert "Required Monthly Contribution: $500.00" in output
    assert "Planned Monthly Contribution: $500.00" in output
    assert "Monthly Contribution Surplus: $0.00" in output
    assert "Projected Completion Date: July 18, 2027" in output
    assert "Summary:" in output
    assert "Recommendation:" in output


def test_render_goal_feasibility_assessment_with_shortfall():
    request = build_request(
        planned_monthly_contribution=Decimal("300.00"),
    )

    projection = build_goal_projection(
        request.goal,
        target_date=request.target_date,
        planned_monthly_contribution=request.planned_monthly_contribution,
        as_of_date=AS_OF_DATE,
    )

    assessment = assess_goal_feasibility(projection)
    output = render_goal_feasibility_assessment(assessment)

    assert "Status: At Risk" in output
    assert "Feasible: No" in output
    assert "Required Monthly Contribution: $500.00" in output
    assert "Planned Monthly Contribution: $300.00" in output
    assert "Monthly Contribution Shortfall: $200.00" in output
    assert "Projected Completion Date:" in output
    assert "Recommendation:" in output


def test_render_goal_allocation():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="Emergency Fund",
        priority=GoalPriority.CRITICAL,
        required_amount=Decimal("500.00"),
        allocated_amount=Decimal("300.00"),
    )

    output = render_goal_allocation(allocation)

    assert "Goal: Emergency Fund" in output
    assert "Priority: Critical" in output
    assert "Required Amount: $500.00" in output
    assert "Allocated Amount: $300.00" in output
    assert "Shortfall: $200.00" in output
    assert "Fully Funded: No" in output


def test_render_goal_allocation_plan():
    result = build_result()
    output = render_goal_allocation_plan(result.allocation_plan)

    assert "MONTHLY GOAL FUNDING ALLOCATION" in output
    assert "Goal: Emergency Fund" in output
    assert "Goal: Car Fund" in output
    assert "Goal: Vacation" in output
    assert "ALLOCATION SUMMARY" in output
    assert "Total Available: $1,000.00" in output
    assert "Total Required: $1,400.00" in output
    assert "Total Allocated: $1,000.00" in output
    assert "Total Shortfall: $400.00" in output
    assert "Remaining Cash: $0.00" in output
    assert "All Goals Funded: No" in output


def test_render_empty_goal_allocation_plan():
    plan = GoalAllocationPlan(
        allocations=[],
        total_available=Decimal("1000.00"),
    )

    output = render_goal_allocation_plan(plan)

    assert "No financial goals were provided for allocation." in output
    assert "Total Available: $1,000.00" in output
    assert "Remaining Cash: $1,000.00" in output
    assert "All Goals Funded: Yes" in output


def test_render_goal_priority_report_uses_priority_funding_order():
    output = render_goal_priority_report(build_result())

    assert "GOAL PRIORITIZATION REPORT" in output
    assert "RECOMMENDED FUNDING ORDER" in output

    emergency_position = output.index("Goal: Emergency Fund")
    car_position = output.index("Goal: Car Fund")
    vacation_position = output.index("Goal: Vacation")

    assert emergency_position < car_position < vacation_position
    assert "Rank 1\nGoal: Emergency Fund\nPriority: Critical" in output
    assert "Rank 2\nGoal: Car Fund\nPriority: High" in output
    assert "Rank 3\nGoal: Vacation\nPriority: Low" in output
    assert "Funding Status: Fully funded" in output
    assert "Funding Status: $100.00 short" in output
    assert "Funding Status: $300.00 short" in output
    assert "Direct the next $100.00 of available monthly cash to Car Fund" in output


def test_render_goal_priority_report_when_all_goals_are_funded():
    output = render_goal_priority_report(
        build_result(
            total_available=Decimal("1400.00"),
        )
    )

    assert "Funding Status: Fully funded" in output
    assert "$100.00 short" not in output
    assert "$300.00 short" not in output
    assert "every goal is fully funded" in output


def test_render_goal_priority_report_without_goals():
    result = analyze_goals(
        [],
        total_available=Decimal("1000.00"),
        as_of_date=AS_OF_DATE,
    )

    output = render_goal_priority_report(result)

    assert "GOAL PRIORITIZATION REPORT" in output
    assert "No goals are available for prioritization." in output
    assert "assign a priority" in output


def test_render_goal_funding_gap_report_with_shortfall():
    output = render_goal_funding_gap_report(build_result())

    assert "MONTHLY FUNDING GAP REPORT" in output
    assert "Monthly Funding Required: $1,400.00" in output
    assert "Monthly Funding Available: $1,000.00" in output
    assert "Monthly Funding Gap: $400.00" in output
    assert "Status: Funding shortfall" in output
    assert "Car Fund (High): $100.00 short" in output
    assert "Vacation (Low): $300.00 short" in output
    assert "Increase monthly goal funding by $400.00" in output


def test_render_goal_funding_gap_report_when_fully_funded():
    output = render_goal_funding_gap_report(
        build_result(
            total_available=Decimal("1400.00"),
        )
    )

    assert "Monthly Funding Gap: $0.00" in output
    assert "Status: Fully funded" in output
    assert "Maintain the current monthly funding level" in output
    assert "GOALS REQUIRING ADDITIONAL FUNDING" not in output


def test_render_goal_funding_gap_report_without_goals():
    result = analyze_goals(
        [],
        total_available=Decimal("1000.00"),
        as_of_date=AS_OF_DATE,
    )

    output = render_goal_funding_gap_report(result)

    assert "Monthly Funding Required: $0.00" in output
    assert "Monthly Funding Available: $1,000.00" in output
    assert "Monthly Funding Gap: $0.00" in output
    assert "Status: No goals available" in output
    assert "Create a financial goal" in output


def test_render_goal_planning_summary():
    output = render_goal_planning_summary(build_result())

    assert "GOAL PLANNING SUMMARY" in output
    assert "Total Goals: 3" in output
    assert "Completed Goals: 0" in output
    assert "Feasible Goals: 1" in output
    assert "At-Risk Goals: 1" in output
    assert "Unfunded Goals: 1" in output
    assert "Missed Deadlines: 0" in output
    assert "Total Monthly Required: $1,400.00" in output
    assert "Total Monthly Allocated: $1,000.00" in output
    assert "Overall Funding Gap: $400.00" in output
    assert "Remaining Monthly Cash: $0.00" in output
    assert "All Goals Feasible: No" in output


def test_render_goal_planning_result():
    output = render_goal_planning_result(build_result())

    assert "FINANCIAL GOAL PLANNING REPORT" in output
    assert "GOAL PLANNING SUMMARY" in output
    assert "GOAL PRIORITIZATION REPORT" in output
    assert "MONTHLY FUNDING GAP REPORT" in output
    assert "Monthly Funding Gap: $400.00" in output
    assert "GOAL PROJECTIONS" in output
    assert "Projection 1" in output
    assert "FEASIBILITY ASSESSMENTS" in output
    assert "Assessment 1" in output
    assert "MONTHLY GOAL FUNDING ALLOCATION" in output
    assert "Goal: Emergency Fund" in output
    assert "Goal: Vacation" in output
    assert "Goal: Car Fund" in output


def test_render_empty_goal_planning_result():
    result = analyze_goals(
        [],
        total_available=Decimal("1000.00"),
        as_of_date=AS_OF_DATE,
    )

    output = render_goal_planning_result(result)

    assert "Total Goals: 0" in output
    assert "GOAL PRIORITIZATION REPORT" in output
    assert "MONTHLY FUNDING GAP REPORT" in output
    assert "No financial goals are available for analysis." in output
    assert "No financial goals were provided for allocation." in output
    assert "Remaining Cash: $1,000.00" in output


def test_render_goal_planning_request_list():
    output = render_goal_planning_request_list(build_standard_requests())

    assert "GOAL PLANNING REQUESTS" in output
    assert "Request 1" in output
    assert "Request 2" in output
    assert "Request 3" in output
    assert "Goal: Emergency Fund" in output
    assert "Goal: Vacation" in output
    assert "Goal: Car Fund" in output


def test_render_empty_goal_planning_request_list():
    output = render_goal_planning_request_list([])

    assert output == "No goal-planning requests are available."
