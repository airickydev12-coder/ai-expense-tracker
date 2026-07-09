from enum import Enum


class RecommendationCategory(Enum):
    """Categories for financial recommendations."""

    CASH_FLOW = "Cash Flow"
    BUDGET = "Budget"
    DEBT = "Debt"
    SAVINGS = "Savings"
    GOALS = "Goals"
    HEALTH = "Health"
    BILLS = "Bills"
    WEALTH = "Wealth"
    INCOME = "Income"
    EXPENSES = "Expenses"