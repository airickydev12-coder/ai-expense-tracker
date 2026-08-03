"""Primary command-line interface controller."""

from src.financial.application.financial_state import (
    record_current_financial_snapshot,
)
from src.financial.expenses.analytics import get_total
from src.financial.expenses.service import get_expenses
from src.presentation.cli_context import get_cli_user_id
from src.financial.goals.service import get_goals
from src.financial.history.service import get_history
from src.financial.scenarios.factory import (
    register_default_scenario_handlers,
)
from src.presentation.budget_cli import manage_budgets
from src.presentation.coach_cli import run_financial_coach
from src.presentation.expense_cli import (
    add_expense_flow,
    delete_expense_flow,
    update_expense_flow,
)
from src.presentation.forecast_cli import (
    display_current_forecast,
)
from src.presentation.goal_planning_cli import (
    run_goal_planning_menu,
)
from src.presentation.main_menu_view import (
    show_main_menu,
)
from src.presentation.recommendation_cli import (
    manage_recommendations,
)
from src.presentation.scenario_cli import (
    manage_scenarios,
)
from src.presentation.views import (
    display_category_totals,
    display_dashboard,
    display_expenses,
    display_financial_snapshot,
    display_financial_trends,
    display_saved_budget_summaries,
)

EXIT_OPTION = "16"


def run_cli() -> None:
    """Run the primary command-line menu."""
    load_financial_state()
    register_default_scenario_handlers()
    display_dashboard()

    while True:
        show_main_menu()

        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_expense_flow()

        elif choice == "2":
            display_expenses()

        elif choice == "3":
            total = get_total(get_expenses())

            print(f"Total spending: ${total:.2f}")

        elif choice == "4":
            delete_expense_flow()

        elif choice == "5":
            update_expense_flow()

        elif choice == "6":
            display_category_totals()

        elif choice == "7":
            manage_budgets()

        elif choice == "8":
            display_saved_budget_summaries()

        elif choice == "9":
            snapshot, _ = record_current_financial_snapshot()

            display_financial_snapshot(snapshot)

            print("\nFinancial snapshot saved " "to history.")

        elif choice == "10":
            manage_recommendations()

        elif choice == "11":
            display_financial_trends(get_history())

        elif choice == "12":
            display_current_forecast()

        elif choice == "13":
            manage_scenarios()

        elif choice == "14":
            run_financial_coach()

        elif choice == "15":
            run_goal_planning_menu(get_goals())

        elif choice == EXIT_OPTION:
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please choose " "a number from 1 through 16.")
