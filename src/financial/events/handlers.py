def log_expense_added(expense) -> None:
    print(f"[EVENT] Expense added: {expense.name}")


def log_income_added(income) -> None:
    print(f"[EVENT] Income added: {income.source}")
