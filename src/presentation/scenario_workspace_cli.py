from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
)
from src.financial.scenarios.workspace import (
    clear_scenario_workspace,
    get_saved_scenario_results,
    scenario_workspace,
)
from src.presentation.views import (
    display_scenario_result,
)


def display_workspace_menu() -> None:
    """Display the scenario workspace menu."""
    print("\nScenario Planning Workspace")
    print("1. View Saved Scenarios")
    print("2. Rank Scenarios")
    print("3. View Best Scenario")
    print("4. Remove Scenario")
    print("5. Clear Workspace")
    print("6. Back")


def select_ranking_metric() -> ScenarioRankingMetric | None:
    """Select a ranking metric."""
    print("\nRanking Metrics")
    print("1. Overall")
    print("2. Net Worth")
    print("3. Cash Flow")
    print("4. Debt Reduction")
    print("5. Improvement Count")
    print("6. Back")

    selection = input("Choose a ranking metric: ").strip()

    metrics = {
        "1": ScenarioRankingMetric.OVERALL,
        "2": ScenarioRankingMetric.NET_WORTH,
        "3": ScenarioRankingMetric.CASH_FLOW,
        "4": ScenarioRankingMetric.DEBT_REDUCTION,
        "5": ScenarioRankingMetric.IMPROVEMENT_COUNT,
    }

    if selection == "6":
        return None

    metric = metrics.get(selection)

    if metric is None:
        print("Invalid ranking option. " "Please choose 1 through 6.")
        return None

    return metric


def display_saved_scenarios() -> None:
    """Display all saved scenario names."""
    results = get_saved_scenario_results()

    if not results:
        print("No scenarios are saved.")
        return

    print("\nSaved Scenarios")

    for index, result in enumerate(
        results,
        start=1,
    ):
        print(f"{index}. {result.name} " f"({result.scenario_type.value})")


def display_ranked_scenarios() -> None:
    """Rank and display saved scenarios."""
    if scenario_workspace.is_empty():
        print("No scenarios are saved.")
        return

    ranking_metric = select_ranking_metric()

    if ranking_metric is None:
        return

    ranked = scenario_workspace.rank(ranking_metric)

    print(f"\nScenario Ranking — " f"{ranking_metric.value}")

    for item in ranked:
        print(f"{item.rank}. {item.scenario_name} | " f"Score: {item.score:,.2f}")


def display_best_scenario() -> None:
    """Display the strongest saved scenario."""
    if scenario_workspace.is_empty():
        print("No scenarios are saved.")
        return

    ranking_metric = select_ranking_metric()

    if ranking_metric is None:
        return

    best = scenario_workspace.best(ranking_metric)

    if best is None:
        print("No scenario could be ranked.")
        return

    print(f"\nBest Scenario by " f"{ranking_metric.value}: " f"{best.scenario_name}")

    display_scenario_result(best.result)


def remove_saved_scenario() -> None:
    """Select and remove one scenario."""
    results = get_saved_scenario_results()

    if not results:
        print("No scenarios are saved.")
        return

    display_saved_scenarios()

    selection_text = input("Choose a scenario to remove: ").strip()

    try:
        selection = int(selection_text)
    except ValueError:
        print("Scenario selection must be a number.")
        return

    if selection < 1 or selection > len(results):
        print("Scenario selection is out of range.")
        return

    removed = scenario_workspace.remove_result(results[selection - 1].name)

    if removed is None:
        print("Scenario was not found.")
        return

    print(f"Removed scenario: {removed.name}")


def clear_workspace_flow() -> None:
    """Confirm and clear the scenario workspace."""
    if scenario_workspace.is_empty():
        print("No scenarios are saved.")
        return

    confirmation = input("Clear all saved scenarios? (y/n): ").strip().lower()

    if confirmation != "y":
        print("Workspace was not cleared.")
        return

    clear_scenario_workspace()
    print("Scenario workspace cleared.")


def manage_scenario_workspace() -> None:
    """Run the scenario workspace menu."""
    while True:
        display_workspace_menu()

        choice = input("Choose an option: ").strip()

        if choice == "1":
            display_saved_scenarios()

        elif choice == "2":
            display_ranked_scenarios()

        elif choice == "3":
            display_best_scenario()

        elif choice == "4":
            remove_saved_scenario()

        elif choice == "5":
            clear_workspace_flow()

        elif choice == "6":
            return

        else:
            print("Invalid workspace option. " "Please choose 1 through 6.")
