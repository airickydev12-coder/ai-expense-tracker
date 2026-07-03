from src.expense_tracker import (
    add_expense,
    view_expenses,
    calculate_total,
    load_expenses,
)


def show_menu():
    print("\nAI Expense Tracker")
    print("1. Add expense")
    print("2. View expenses")
    print("3. View total spending")
    print("4. Exit")


def main():
    load_expenses()

    while True:
        show_menu()
        choice = input("Choose an option: ")

        if choice == "1":
            add_expense()
        elif choice == "2":
            view_expenses()
        elif choice == "3":
            calculate_total()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()