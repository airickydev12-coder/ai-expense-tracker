expenses = []
import json
from pathlib import Path


DATA_FILE = Path("data/expenses.json")
expenses = []


def load_expenses():
    global expenses

    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as file:
            expenses = json.load(file)


def save_expenses():
    with open(DATA_FILE, "w") as file:
        json.dump(expenses, file, indent=4)

def add_expense():
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


def view_expenses():
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


def calculate_total():
    total = 0

    for expense in expenses:
        total += expense["amount"]

    print(f"Total spending: ${total:.2f}")