from enum import Enum


class ExpenseCategory(str, Enum):
    """Supported expense categories."""

    FOOD = "Food"
    TRANSPORTATION = "Transportation"
    HOUSING = "Housing"
    UTILITIES = "Utilities"
    HEALTHCARE = "Healthcare"
    CLOTHING = "Clothing"
    MAINTENANCE = "Maintenance"
    ENTERTAINMENT = "Entertainment"
    EDUCATION = "Education"
    INSURANCE = "Insurance"
    SAVINGS = "Savings"
    OTHER = "Other"
