expenses = []


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