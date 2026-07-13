from src.financial.application.financial_state import (
    build_current_financial_snapshot,
    load_financial_state,
    record_current_financial_snapshot,
)
from src.financial.budgets.analytics import get_budget_summary
from src.financial.budgets.service import add_budget, delete_budget
from src.financial.expenses.analytics import get_total
from src.financial.expenses.service import (
    add_expense,
    delete_expense,
    get_expenses,
    update_expense,
)
from src.financial.history.service import get_history
from src.financial.recommendations.history import RecommendationRecord
from src.financial.recommendations.history_service import (
    activate_recommendation,
    complete_recommendation,
    dismiss_recommendation,
    get_recommendation_history,
    suppress_recommendation,
)
from src.presentation.input_handlers import select_category
from src.presentation.views import (
    display_budget_summary,
    display_category_totals,
    display_current_budgets,
    display_dashboard,
    display_expenses,
    display_financial_snapshot,
    display_financial_trends,
    display_recommendation_history,
    display_recommendation_management_menu,
    display_recommendations,
    display_saved_budget_summaries,
    show_menu,
)


def select_recommendation_key(
    recommendations: list[dict],
) -> str | None:
    """Select a recommendation key from serialized recommendations."""
    if not recommendations:
        print("No active recommendations are available.")
        return None

    display_recommendations(recommendations)

    selection_text = input(
        "Enter the recommendation number: "
    ).strip()

    try:
        selection = int(selection_text)
    except ValueError:
        print("Invalid selection. Please enter a number.")
        return None

    if selection < 1 or selection > len(recommendations):
        print("Recommendation selection is out of range.")
        return None

    recommendation = recommendations[selection - 1]
    recommendation_key = recommendation.get("key")

    if not recommendation_key:
        print("The selected recommendation has no key.")
        return None

    return str(recommendation_key)


def select_history_record_key(
    records: list[RecommendationRecord],
) -> str | None:
    """Select a recommendation key from lifecycle history."""
    if not records:
        print("No recommendation history is available.")
        return None

    display_recommendation_history(records)

    selection_text = input(
        "Enter the history record number: "
    ).strip()

    try:
        selection = int(selection_text)
    except ValueError:
        print("Invalid selection. Please enter a number.")
        return None

    if selection < 1 or selection > len(records):
        print("History selection is out of range.")
        return None

    sorted_records = sorted(
        records,
        key=lambda record: record.updated_at,
        reverse=True,
    )

    return sorted_records[selection - 1].recommendation_key


def manage_recommendations() -> None:
    """Run the recommendation-management submenu."""
    while True:
        display_recommendation_management_menu()

        recommendation_choice = input(
            "Choose an option: "
        ).strip()

        snapshot = build_current_financial_snapshot()
        active_recommendations = snapshot.get(
            "recommendations",
            [],
        )
        history = get_recommendation_history()

        if recommendation_choice == "1":
            display_recommendations(
                active_recommendations
            )

        elif recommendation_choice == "2":
            display_recommendation_history(
                history
            )

        elif recommendation_choice == "3":
            recommendation_key = select_history_record_key(
                history
            )

            if recommendation_key is None:
                continue

            note = input(
                "Optional note: "
            ).strip()

            record = activate_recommendation(
                recommendation_key,
                note=note,
            )

            if record is None:
                print("Recommendation record not found.")
            else:
                print("Recommendation marked as active.")

        elif recommendation_choice == "4":
            recommendation_key = select_recommendation_key(
                active_recommendations
            )

            if recommendation_key is None:
                continue

            note = input(
                "Optional completion note: "
            ).strip()

            record = complete_recommendation(
                recommendation_key,
                note=note,
            )

            if record is None:
                print("Recommendation record not found.")
            else:
                print("Recommendation marked as completed.")

        elif recommendation_choice == "5":
            recommendation_key = select_recommendation_key(
                active_recommendations
            )

            if recommendation_key is None:
                continue

            note = input(
                "Optional dismissal note: "
            ).strip()

            record = dismiss_recommendation(
                recommendation_key,
                note=note,
            )

            if record is None:
                print("Recommendation record not found.")
            else:
                print("Recommendation dismissed.")

        elif recommendation_choice == "6":
            recommendation_key = select_recommendation_key(
                active_recommendations
            )

            if recommendation_key is None:
                continue

            note = input(
                "Optional suppression note: "
            ).strip()

            record = suppress_recommendation(
                recommendation_key,
                note=note,
            )

            if record is None:
                print("Recommendation record not found.")
            else:
                print("Recommendation suppressed.")

        elif recommendation_choice == "7":
            break

        else:
            print(
                "Invalid recommendation option. "
                "Please choose 1 through 7."
            )


def run_cli() -> None:
    """Run the command-line interface."""
    load_financial_state()
    display_dashboard()

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            name = input("Expense name: ").strip()
            category = select_category()

            if category is None:
                continue

            amount_text = input("Amount: ").strip()

            try:
                amount = float(amount_text)
            except ValueError:
                print("Invalid amount. Please enter a number.")
                continue

            if amount < 0:
                print("Amount cannot be negative.")
                continue

            add_expense(
                name,
                category,
                amount,
            )

            print("Expense added successfully!")

        elif choice == "2":
            display_expenses()

        elif choice == "3":
            total = get_total(get_expenses())
            print(f"Total spending: ${total:.2f}")

        elif choice == "4":
            display_expenses()

            expense_id_text = input(
                "Enter the expense ID to delete: "
            ).strip()

            try:
                expense_id = int(expense_id_text)
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            deleted_expense = delete_expense(expense_id)

            if deleted_expense is None:
                print("Expense not found.")
            else:
                print(
                    f"Deleted expense: "
                    f"{deleted_expense.name}"
                )

        elif choice == "5":
            display_expenses()

            expense_id_text = input(
                "Enter the expense ID to update: "
            ).strip()

            try:
                expense_id = int(expense_id_text)
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            new_name = input(
                "New name "
                "(press Enter to keep unchanged): "
            )

            category_input = input(
                "Change category? (y/n): "
            ).lower().strip()

            category = None

            if category_input == "y":
                category = select_category()

                if category is None:
                    continue

            new_amount_text = input(
                "New amount "
                "(press Enter to keep unchanged): "
            ).strip()

            name = (
                new_name.strip()
                if new_name.strip()
                else None
            )

            amount = None

            if new_amount_text:
                try:
                    amount = float(new_amount_text)
                except ValueError:
                    print(
                        "Invalid amount. "
                        "Please enter a number."
                    )
                    continue

                if amount < 0:
                    print("Amount cannot be negative.")
                    continue

            updated_expense = update_expense(
                expense_id=expense_id,
                name=name,
                category=category,
                amount=amount,
            )

            if updated_expense is None:
                print("Expense not found.")
            else:
                print(
                    f"Updated expense: "
                    f"{updated_expense.name}"
                )

        elif choice == "6":
            display_category_totals()

        elif choice == "7":
            display_current_budgets()

            print("\nManage Budgets")
            print("1. Create / Update Budgets")
            print("2. Delete Budget")
            print("3. Back")

            budget_choice = input(
                "Choose an option: "
            ).strip()

            if budget_choice == "1":
                while True:
                    print("\nCreate / Update Budget")

                    category = select_category()

                    if category is None:
                        retry = input(
                            "Try selecting a category "
                            "again? (y/n): "
                        ).strip().lower()

                        if retry != "y":
                            break

                        continue

                    limit_text = input(
                        "Enter budget limit: "
                    ).strip()

                    try:
                        limit = float(limit_text)
                    except ValueError:
                        print(
                            "Invalid budget limit. "
                            "Please enter a number."
                        )
                        continue

                    if limit <= 0:
                        print(
                            "Budget limit must be "
                            "greater than zero."
                        )
                        continue

                    budget = add_budget(
                        category,
                        limit,
                    )

                    summary = get_budget_summary(
                        budget,
                        get_expenses(),
                    )

                    print("\nBudget saved successfully.")
                    display_budget_summary(summary)

                    add_another = input(
                        "\nCreate or update another "
                        "budget? (y/n): "
                    ).strip().lower()

                    if add_another != "y":
                        break

            elif budget_choice == "2":
                category = select_category()

                if category is None:
                    continue

                deleted_budget = delete_budget(
                    category
                )

                if deleted_budget is None:
                    print("Budget not found.")
                else:
                    print(
                        "Deleted budget for "
                        f"{deleted_budget.category.value}."
                    )

            elif budget_choice == "3":
                continue

            else:
                print("Invalid budget option.")

        elif choice == "8":
            display_saved_budget_summaries()

        elif choice == "9":
            snapshot, _ = (
                record_current_financial_snapshot()
            )

            display_financial_snapshot(snapshot)
            print(
                "\nFinancial snapshot saved to history."
            )

        elif choice == "10":
            manage_recommendations()

        elif choice == "11":
            display_financial_trends(
                get_history()
            )

        elif choice == "12":
            print("Goodbye!")
            break

        else:
            print(
                "Invalid option. Please choose "
                "1, 2, 3, 4, 5, 6, 7, 8, "
                "9, 10, 11, or 12."
            )