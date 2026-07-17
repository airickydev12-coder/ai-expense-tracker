from src.financial.application.financial_state import (
    build_current_financial_snapshot,
)
from src.financial.coach.coaching import (
    CoachingSession,
    build_coaching_session,
)
from src.financial.scenarios.optimizer import (
    optimize_financial_snapshot,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
)
from src.presentation.coach_views import (
    display_complete_coaching_session,
)


def build_current_coaching_session(
    *,
    advice_limit: int = 3,
    next_step_limit: int = 5,
    optimization_limit: int = 5,
    horizon_months: int = 12,
) -> CoachingSession:
    """Build a coaching session from current financial state."""
    snapshot = build_current_financial_snapshot()

    optimization_result = optimize_financial_snapshot(
        snapshot,
        ranking_metric=(ScenarioRankingMetric.OVERALL),
        limit=optimization_limit,
        horizon_months=horizon_months,
    )

    return build_coaching_session(
        snapshot,
        optimization_result,
        advice_limit=advice_limit,
        next_step_limit=next_step_limit,
    )


def run_financial_coach() -> None:
    """Build and display the current coaching session."""
    print("\nAnalyzing your financial position...")

    try:
        session = build_current_coaching_session()
    except ValueError as error:
        print(f"\nUnable to build financial " f"coaching session: {error}")
        return

    display_complete_coaching_session(session)
