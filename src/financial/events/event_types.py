from enum import Enum


class FinancialEvent(Enum):
    EXPENSE_ADDED = "expense_added"
    EXPENSE_UPDATED = "expense_updated"
    EXPENSE_DELETED = "expense_deleted"
    INCOME_ADDED = "income_added"
    BILL_PAID = "bill_paid"
    BUDGET_UPDATED = "budget_updated"
    GOAL_UPDATED = "goal_updated"
    DEBT_PAYMENT = "debt_payment"