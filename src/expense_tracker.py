expenses = []
import json
from pathlib import Path


DATA_FILE = Path("data/expenses.json")
expenses = []


def load_expenses() -> None:
    """
    Load expenses from the JSON data file.

    Checks whether the data file exists and, if it does, reads
    the stored expenses from the JSON file and assigns them to
    the global expenses list.

    If the data file does not exist, the expenses list remains
    unchanged.

    Returns:
        None
    """
    global expenses

    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as file:
            expenses = json.load(file)


def save_expenses() -> None:
    """
    Save all recorded expenses to the JSON data file.

    Writes the current contents of the expenses list to the
    JSON file specified by DATA_FILE. The data is formatted
    with indentation to make the file more readable.

    Returns:
        None
    """
    with open(DATA_FILE, "w") as file:
        json.dump(expenses, file, indent=4)

def add_expense() -> None:
    """
    Add a new expense to the expense tracker.

    Prompts the user to enter an expense name, category, and amount.
    The amount is validated to ensure it can be converted to a float.
    If the amount is invalid, an error message is displayed and the
    expense is not added.

    When a valid expense is entered, it is added to the expenses list,
    saved to the JSON file, and a confirmation message is displayed.

    Returns:
        None
    """
    name = input("Expense name: ")
    category = input("Category: ")
    amount_text = input("Amount: ")

    try:
        amount = float(amount_text)
    except ValueError:
        print("Invalid amount. Please enter a number.")
        return

    expense = {
        "name": name,
        "category": category,
        "amount": amount,
    }

    expenses.append(expense)
    save_expenses()
    print("Expense added successfully!")


def view_expenses() -> None:
    """
    Display all recorded expenses.

    Prints each expense in the expenses list along with its
    number, name, category, and amount formatted as currency.

    If no expenses have been recorded, a message is displayed
    informing the user that there are no expenses to view.

    Returns:
        None
    """
    if not expenses:
        print("No expenses recorded yet.")
        return

    print("\nExpenses:")
    for index, expense in enumerate(expenses, start=1):
        print(
            f"{index}. {expense['name']} | "
            f"{expense['category']} | "
            f"${expense['amount']:.2f}"
        )
def delete_expense() -> None:
    """
    Delete an expense from the expense tracker.

    Displays all recorded expenses and prompts the user to select
    an expense to delete by its number. The function validates that
    the input is numeric and that the selected expense exists.

    If a valid expense is selected, it is removed from the expenses
    list, the updated expenses are saved to the JSON file, and a
    confirmation message is displayed.

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

    print(f"Deleted expense: {deleted_expense['name']}")

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

    new_name = input(f"Name [{expense['name']}]: ")
    new_category = input(f"Category [{expense['category']}]: ")
    new_amount_text = input(f"Amount [{expense['amount']:.2f}]: ")

    if new_name.strip():
        expense["name"] = new_name.strip()

    if new_category.strip():
        expense["category"] = new_category.strip()

    if new_amount_text.strip():
        try:
            new_amount = float(new_amount_text)
        except ValueError:
            print("Invalid amount. Please enter a number.")
            return

        if new_amount < 0:
            print("Amount cannot be negative.")
            return

        expense["amount"] = new_amount

    save_expenses()
    print("Expense updated successfully!")

def get_total() -> float:
    """
    Calculate the total amount of all recorded expenses.

    Returns:
        float: The total amount of all expenses.
    """
    total = 0

    for expense in expenses:
        total += expense["amount"]

    return total


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

