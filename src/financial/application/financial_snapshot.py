"""Models representing consolidated financial application state."""

from dataclasses import dataclass
from decimal import Decimal

from src.financial.accounts.models import Account
from src.financial.bills.models import Bill
from src.financial.debt.models import Debt
from src.financial.expenses.models import Expense
from src.financial.goals.models import Goal


@dataclass(frozen=True)
class FinancialSnapshot:
    """
    Represent the user's current financial state.

    The snapshot contains financial facts only. It intentionally excludes
    insights, recommendations, coaching content, forecasts, and simulations.
    """

    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal

    average_expense: Decimal
    highest_expense: Expense | None
    lowest_expense: Expense | None
    category_totals: dict[str, Decimal]

    budget_count: int
    goal_count: int
    budget_report: list[dict]

    total_account_balance: Decimal
    total_goal_progress: Decimal
    total_debt: Decimal
    net_worth: Decimal

    accounts: list[Account]
    goals: list[Goal]
    debts: list[Debt]
    bills: list[Bill]

    current_day: int

    health_score: int
    health_status: str

    def to_dict(self) -> dict:
        """
        Convert the snapshot to a dictionary.

        This method provides a boundary representation for APIs, rule engines,
        persistence adapters, and temporary backward-compatibility wrappers.
        """

        highest_expense = (
            {
                "id": self.highest_expense.id,
                "name": self.highest_expense.name,
                "category": self.highest_expense.category.value,
                "amount": self.highest_expense.amount,
            }
            if self.highest_expense is not None
            else None
        )

        lowest_expense = (
            {
                "id": self.lowest_expense.id,
                "name": self.lowest_expense.name,
                "category": self.lowest_expense.category.value,
                "amount": self.lowest_expense.amount,
            }
            if self.lowest_expense is not None
            else None
        )

        return {
            "total_income": self.total_income,
            "total_expenses": self.total_expenses,
            "net_cash_flow": self.net_cash_flow,
            "average_expense": self.average_expense,
            "largest_expense": highest_expense,
            "lowest_expense": lowest_expense,
            "category_totals": self.category_totals.copy(),
            "budget_count": self.budget_count,
            "goal_count": self.goal_count,
            "budget_report": [item.copy() for item in self.budget_report],
            "total_account_balance": self.total_account_balance,
            "total_goal_progress": self.total_goal_progress,
            "total_debt": self.total_debt,
            "net_worth": self.net_worth,
            "health_score": self.health_score,
            "health_status": self.health_status,
            "accounts": [
                {
                    "id": account.id,
                    "name": account.name,
                    "account_type": account.account_type,
                    "balance": account.balance,
                }
                for account in self.accounts
            ],
            "goals": [
                {
                    "id": goal.id,
                    "name": goal.name,
                    "target_amount": goal.target_amount,
                    "current_amount": goal.current_amount,
                }
                for goal in self.goals
            ],
            "debts": [
                {
                    "id": debt.id,
                    "name": debt.name,
                    "balance": debt.balance,
                    "interest_rate": debt.interest_rate,
                    "minimum_payment": debt.minimum_payment,
                }
                for debt in self.debts
            ],
            "bills": [
                {
                    "id": bill.id,
                    "name": bill.name,
                    "amount": bill.amount,
                    "due_day": bill.due_day,
                    "is_paid": bill.is_paid,
                }
                for bill in self.bills
            ],
            "current_day": self.current_day,
        }
