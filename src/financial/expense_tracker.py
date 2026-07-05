import json

from src.core.config import DATA_FILE
from src.financial.models import Expense

expenses: list[Expense] = []


def load_expenses() -> None:
    """
    Load expenses from the JSON data file.

    Reads the stored expense data from the JSON file and converts
    each dictionary into an Expense object using Expense.from_dict().

    Returns:
        None
    """
    global expenses

    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as file:
            raw_data = json.load(file)

        expenses = [Expense.from_dict(item) for item in raw_data]


def save_expenses() -> None:
    """
    Save all recorded expenses to the JSON data file.

    Converts each Expense object into a dictionary using
    Expense.to_dict() and writes the resulting list to the
    JSON file.

    Returns:
        None
    """
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = [expense.to_dict() for expense in expenses]

    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)


def add_expense(name: str, category: str, amount: float) -> Expense:
    """
    Create and add a new expense.

    Args:
        name: The name of the expense.
        category: The expense category.
        amount: The expense amount.

    Returns:
        Expense: The newly created Expense object.
    """
    expense = Expense(name=name, category=category, amount=amount)

    expenses.append(expense)
    save_expenses()

    return expense


def view_expenses() -> None:
    """
    Display all recorded expenses.

    Prints each expense in the expenses list along with its
    number, name, category, and amount formatted as currency.

    Returns:
        None
    """
    if not expenses:
        print("No expenses recorded yet.")
        return

    print("\nExpenses:")
    for index, expense in enumerate(expenses, start=1):
        print(
            f"{index}. {expense.name} | "
            f"{expense.category} | "
            f"${expense.amount:.2f}"
        )


def delete_expense() -> None:
    """
    Delete an expense from the expense tracker.

    Displays all recorded expenses and prompts the user to select
    an expense to delete by its number.

    Returns:
        None
    """
    if not expenses:
        print("No expenses to delete.")
        return

    view_expenses()

    choice = input("Enter the expense number to delete: ")

    try:
        index = int(choice) - 1
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    if index < 0 or index >= len(expenses):
        print("Invalid expense number.")
        return

    deleted_expense = expenses.pop(index)
    save_expenses()

    print(f"Deleted expense: {deleted_expense.name}")


def update_expense() -> None:
    """
    Update an existing expense.

    Displays recorded expenses, lets the user select one by number,
    and allows the name, category, or amount to be changed. Pressing
    Enter keeps the current value.

    Returns:
        None
    """
    if not expenses:
        print("No expenses to update.")
        return

    view_expenses()

    choice = input("Enter the expense number to update: ")

    try:
        index = int(choice) - 1
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    if index < 0 or index >= len(expenses):
        print("Invalid expense number.")
        return

    expense = expenses[index]

    print("Press Enter to keep the current value.")

    new_name = input(f"Name [{expense.name}]: ")
    new_category = input(f"Category [{expense.category}]: ")
    new_amount_text = input(f"Amount [{expense.amount:.2f}]: ")

    if new_name.strip():
        expense.name = new_name.strip()

    if new_category.strip():
        expense.category = new_category.strip()

    if new_amount_text.strip():
        try:
            new_amount = float(new_amount_text)
        except ValueError:
            print("Invalid amount. Please enter a number.")
            return

        if new_amount < 0:
            print("Amount cannot be negative.")
            return

        expense.amount = new_amount

    save_expenses()
    print("Expense updated successfully!")


def get_total() -> float:
    """
    Calculate the total amount of all recorded expenses.

    Returns:
        float: The total amount of all expenses.
    """
    return sum(expense.amount for expense in expenses)


def calculate_total() -> None:
    """
    Display the total amount of all recorded expenses.

    Retrieves the total spending by calling the get_total()
    function and prints the result formatted as currency.

    Returns:
        None
    """
    total = get_total()
    print(f"Total spending: ${total:.2f}")
