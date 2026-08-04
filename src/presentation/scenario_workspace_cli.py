from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
)
from src.financial.scenarios.workspace_service import (
    clear_persisted_scenario_workspace,
    get_scenario_workspace,
    remove_result_from_workspace,
    save_scenario_workspace,
)
from src.presentation.cli_context import get_cli_user_id
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
    print("5. Save Workspace")
    print("6. Clear Workspace")
    print("7. Back")


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
    workspace = get_scenario_workspace(get_cli_user_id())
    results = workspace.get_results()

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
    workspace = get_scenario_workspace(get_cli_user_id())

    if workspace.is_empty():
        print("No scenarios are saved.")
        return

    ranking_metric = select_ranking_metric()

    if ranking_metric is None:
        return

    ranked = workspace.rank(ranking_metric)

    print(f"\nScenario Ranking — " f"{ranking_metric.value}")

    for item in ranked:
        print(f"{item.rank}. {item.scenario_name} | " f"Score: {item.score:,.2f}")


def display_best_scenario() -> None:
    """Display the strongest saved scenario."""
    workspace = get_scenario_workspace(get_cli_user_id())

    if workspace.is_empty():
        print("No scenarios are saved.")
        return

    ranking_metric = select_ranking_metric()

    if ranking_metric is None:
        return

    best = workspace.best(ranking_metric)

    if best is None:
        print("No scenario could be ranked.")
        return

    print(f"\nBest Scenario by " f"{ranking_metric.value}: " f"{best.scenario_name}")

    display_scenario_result(best.result)


def remove_saved_scenario() -> None:
    """Select and remove one persisted scenario."""
    workspace = get_scenario_workspace(get_cli_user_id())
    results = workspace.get_results()

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

    removed = remove_result_from_workspace(get_cli_user_id(), results[selection - 1].name)

    if removed is None:
        print("Scenario was not found.")
        return

    print(f"Removed scenario: {removed.name}")


def save_workspace_flow() -> None:
    """Persist the current scenario workspace."""
    workspace = get_scenario_workspace(get_cli_user_id())

    if workspace.is_empty():
        print("No scenarios are saved.")
        return

    save_scenario_workspace(get_cli_user_id())

    print("Scenario workspace saved successfully.")


def clear_workspace_flow() -> None:
    """Confirm and clear persisted workspace data."""
    workspace = get_scenario_workspace(get_cli_user_id())

    if workspace.is_empty():
        print("No scenarios are saved.")
        return

    confirmation = input("Clear all saved scenarios? (y/n): ").strip().lower()

    if confirmation != "y":
        print("Workspace was not cleared.")
        return

    clear_persisted_scenario_workspace(get_cli_user_id())

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
            save_workspace_flow()

        elif choice == "6":
            clear_workspace_flow()

        elif choice == "7":
            return

        else:
            print("Invalid workspace option. " "Please choose 1 through 7.")
