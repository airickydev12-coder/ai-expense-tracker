from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.core.money import money_from_json, money_to_json, to_money


@dataclass
class FinancialSnapshotRecord:
    """Represents one historical financial snapshot."""

    timestamp: datetime

    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal

    total_account_balance: Decimal
    total_goal_progress: Decimal
    total_debt: Decimal

    net_worth: Decimal

    health_score: int
    health_status: str

    def __post_init__(self) -> None:
        """Normalize monetary fields to Decimal."""
        self.total_income = to_money(self.total_income)
        self.total_expenses = to_money(self.total_expenses)
        self.net_cash_flow = to_money(self.net_cash_flow)
        self.total_account_balance = to_money(self.total_account_balance)
        self.total_goal_progress = to_money(self.total_goal_progress)
        self.total_debt = to_money(self.total_debt)
        self.net_worth = to_money(self.net_worth)

    def to_dict(self) -> dict:
        """Convert the snapshot to a dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_income": money_to_json(self.total_income),
            "total_expenses": money_to_json(self.total_expenses),
            "net_cash_flow": money_to_json(self.net_cash_flow),
            "total_account_balance": money_to_json(self.total_account_balance),
            "total_goal_progress": money_to_json(self.total_goal_progress),
            "total_debt": money_to_json(self.total_debt),
            "net_worth": money_to_json(self.net_worth),
            "health_score": self.health_score,
            "health_status": self.health_status,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> "FinancialSnapshotRecord":
        """Create a snapshot from JSON."""
        return cls(
            timestamp=datetime.fromisoformat(
                data["timestamp"]
            ),
            total_income=money_from_json(str(data["total_income"])),
            total_expenses=money_from_json(str(data["total_expenses"])),
            net_cash_flow=money_from_json(str(data["net_cash_flow"])),
            total_account_balance=money_from_json(
                str(data["total_account_balance"])
            ),
            total_goal_progress=money_from_json(
                str(data["total_goal_progress"])
            ),
            total_debt=money_from_json(
                str(data["total_debt"])
            ),
            net_worth=money_from_json(
                str(data["net_worth"])
            ),
            health_score=int(
                data["health_score"]
            ),
            health_status=data["health_status"],
        )