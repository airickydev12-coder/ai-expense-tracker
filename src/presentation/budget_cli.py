from decimal import Decimal, InvalidOperation

from src.financial.budgets.analytics import get_budget_summary
from src.financial.budgets.service import (
    add_budget,
    delete_budget,
)
from src.financial.expenses.service import get_expenses
from src.presentation.cli_context import get_cli_user_id
from src.presentation.input_handlers import select_category
from src.presentation.views import (
    display_budget_summary,
    display_current_budgets,
)


def create_or_update_budgets() -> None:
    """Create or update multiple category budgets."""
    while True:
        print("\nCreate / Update Budget")

        category = select_category()

        if category is None:
            retry = input("Try selecting a category again? (y/n): ").strip().lower()

            if retry != "y":
                return

            continue

        limit_text = input("Enter budget limit: ").strip()

        try:
            limit = Decimal(limit_text)
        except InvalidOperation, ValueError:
            print("Invalid budget limit. " "Please enter a number.")
            continue

        if limit <= 0:
            print("Budget limit must be greater than zero.")
            continue

        budget = add_budget(
            get_cli_user_id(),
            category,
            limit,
        )

        summary = get_budget_summary(
            budget,
            get_expenses(get_cli_user_id()),
        )

        print("\nBudget saved successfully.")
        display_budget_summary(summary)

        add_another = (
            input("\nCreate or update another budget? (y/n): ").strip().lower()
        )

        if add_another != "y":
            return


def delete_budget_flow() -> None:
    """Select and delete a category budget."""
    category = select_category()

    if category is None:
        return

    deleted_budget = delete_budget(get_cli_user_id(), category)

    if deleted_budget is None:
        print("Budget not found.")
        return

    print("Deleted budget for " f"{deleted_budget.category.value}.")


def manage_budgets() -> None:
    """Run the budget-management submenu."""
    display_current_budgets()

    print("\nManage Budgets")
    print("1. Create / Update Budgets")
    print("2. Delete Budget")
    print("3. Back")

    budget_choice = input("Choose an option: ").strip()

    if budget_choice == "1":
        create_or_update_budgets()

    elif budget_choice == "2":
        delete_budget_flow()

    elif budget_choice == "3":
        return

    else:
        print("Invalid budget option.")
