from src.financial.expense_tracker import (
    add_expense,
    view_expenses,
    calculate_total,
    load_expenses,
    delete_expense,
    update_expense,
)


def show_menu() -> None:
    """Display the main menu."""
    print("\nFinancial Core")
    print("1. Add expense")
    print("2. View expenses")
    print("3. View total spending")
    print("4. Delete expense")
    print("5. Update expense")
    print("6. Exit")


def run_cli() -> None:
    """Run the command-line interface."""
    load_expenses()

    while True:
        show_menu()
        choice = input("Choose an option: ")

        if choice == "1":
            name = input("Expense name: ")
            category = input("Category: ")
            amount_text = input("Amount: ")

            try:
                amount = float(amount_text)
            except ValueError:
                print("Invalid amount. Please enter a number.")
                continue

            add_expense(name, category, amount)
            print("Expense added successfully!")

        elif choice == "2":
            view_expenses()

        elif choice == "3":
            calculate_total()

        elif choice == "4":
            view_expenses()

            expense_id_text = input("Enter the expense ID to delete: ")

            try:
                expense_id = int(expense_id_text)
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            deleted_expense = delete_expense(expense_id)

            if deleted_expense is None:
                print("Expense not found.")
            else:
                print(f"Deleted expense: {deleted_expense.name}")

        elif choice == "5":
            update_expense()

        elif choice == "6":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please choose 1, 2, 3, 4, 5, or 6.")