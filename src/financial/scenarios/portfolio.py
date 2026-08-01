from dataclasses import dataclass

from src.core.exceptions import ValidationError
from src.financial.scenarios.models import ScenarioResult
from src.financial.scenarios.ranking import (
    RankedScenario,
    ScenarioRankingMetric,
    get_best_scenario,
    rank_scenarios,
)


@dataclass(frozen=True)
class ScenarioPortfolio:
    """Represents a collection of comparable scenarios."""

    name: str
    results: list[ScenarioResult]

    def __post_init__(self) -> None:
        """Validate and protect portfolio data."""
        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValidationError("Scenario portfolio name cannot be empty.")

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )

        object.__setattr__(
            self,
            "results",
            self.results.copy(),
        )

    def add_result(
        self,
        result: ScenarioResult,
    ) -> "ScenarioPortfolio":
        """Return a new portfolio containing the result."""
        return ScenarioPortfolio(
            name=self.name,
            results=[
                *self.results,
                result,
            ],
        )

    def remove_result(
        self,
        scenario_name: str,
    ) -> "ScenarioPortfolio":
        """Return a new portfolio without the named scenario."""
        normalized_name = scenario_name.strip().lower()

        return ScenarioPortfolio(
            name=self.name,
            results=[
                result
                for result in self.results
                if result.name.lower() != normalized_name
            ],
        )

    def get_result(
        self,
        scenario_name: str,
    ) -> ScenarioResult | None:
        """Return a scenario result by name."""
        normalized_name = scenario_name.strip().lower()

        for result in self.results:
            if result.name.lower() == normalized_name:
                return result

        return None

    def rank(
        self,
        ranking_metric: ScenarioRankingMetric = (ScenarioRankingMetric.OVERALL),
    ) -> list[RankedScenario]:
        """Rank all scenarios in the portfolio."""
        return rank_scenarios(
            self.results,
            ranking_metric,
        )

    def best(
        self,
        ranking_metric: ScenarioRankingMetric = (ScenarioRankingMetric.OVERALL),
    ) -> RankedScenario | None:
        """Return the strongest scenario in the portfolio."""
        return get_best_scenario(
            self.results,
            ranking_metric,
        )

    def to_dict(self) -> dict:
        """Convert the portfolio to a dictionary."""
        return {
            "name": self.name,
            "results": [result.to_dict() for result in self.results],
        }


def build_scenario_portfolio(
    name: str,
    results: list[ScenarioResult],
) -> ScenarioPortfolio:
    """Create a validated scenario portfolio."""
    return ScenarioPortfolio(
        name=name,
        results=results,
    )
