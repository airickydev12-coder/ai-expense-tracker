from dataclasses import dataclass, field

from src.financial.scenarios.models import ScenarioResult
from src.financial.scenarios.portfolio import ScenarioPortfolio
from src.financial.scenarios.ranking import (
    RankedScenario,
    ScenarioRankingMetric,
)


@dataclass
class ScenarioWorkspace:
    """Stores scenario results for the current planning session."""

    name: str = "Current Planning Session"
    _results: list[ScenarioResult] = field(
        default_factory=list,
    )

    def add_result(
        self,
        result: ScenarioResult,
    ) -> None:
        """Add or replace a scenario result by name."""
        normalized_name = result.name.strip().lower()

        self._results = [
            existing
            for existing in self._results
            if existing.name.strip().lower() != normalized_name
        ]

        self._results.append(result)

    def get_results(
        self,
    ) -> list[ScenarioResult]:
        """Return a copy of all stored scenario results."""
        return self._results.copy()

    def get_result(
        self,
        scenario_name: str,
    ) -> ScenarioResult | None:
        """Return a stored scenario result by name."""
        normalized_name = scenario_name.strip().lower()

        for result in self._results:
            if result.name.strip().lower() == normalized_name:
                return result

        return None

    def remove_result(
        self,
        scenario_name: str,
    ) -> ScenarioResult | None:
        """Remove and return a scenario result by name."""
        normalized_name = scenario_name.strip().lower()

        for index, result in enumerate(self._results):
            if result.name.strip().lower() == normalized_name:
                return self._results.pop(index)

        return None

    def clear(
        self,
    ) -> None:
        """Remove all stored scenario results."""
        self._results.clear()

    def count(
        self,
    ) -> int:
        """Return the number of stored scenarios."""
        return len(self._results)

    def is_empty(
        self,
    ) -> bool:
        """Return whether the workspace has no results."""
        return not self._results

    def build_portfolio(
        self,
    ) -> ScenarioPortfolio:
        """Build a portfolio from the current workspace."""
        return ScenarioPortfolio(
            name=self.name,
            results=self.get_results(),
        )

    def rank(
        self,
        ranking_metric: ScenarioRankingMetric = (ScenarioRankingMetric.OVERALL),
    ) -> list[RankedScenario]:
        """Rank all stored scenarios."""
        return self.build_portfolio().rank(ranking_metric)

    def best(
        self,
        ranking_metric: ScenarioRankingMetric = (ScenarioRankingMetric.OVERALL),
    ) -> RankedScenario | None:
        """Return the strongest stored scenario."""
        return self.build_portfolio().best(ranking_metric)


scenario_workspace = ScenarioWorkspace()


def save_scenario_result(
    result: ScenarioResult,
) -> None:
    """Save a result to the shared workspace."""
    scenario_workspace.add_result(result)


def get_saved_scenario_results() -> list[ScenarioResult]:
    """Return all results from the shared workspace."""
    return scenario_workspace.get_results()


def clear_scenario_workspace() -> None:
    """Clear the shared scenario workspace."""
    scenario_workspace.clear()
