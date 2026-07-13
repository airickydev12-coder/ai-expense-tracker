from dataclasses import dataclass
from datetime import datetime


@dataclass
class FinancialSnapshotRecord:
    """Represents one historical financial snapshot."""

    timestamp: datetime

    total_income: float
    total_expenses: float
    net_cash_flow: float

    total_account_balance: float
    total_goal_progress: float
    total_debt: float

    net_worth: float

    health_score: int
    health_status: str

    def to_dict(self) -> dict:
        """Convert the snapshot to a dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_income": self.total_income,
            "total_expenses": self.total_expenses,
            "net_cash_flow": self.net_cash_flow,
            "total_account_balance": self.total_account_balance,
            "total_goal_progress": self.total_goal_progress,
            "total_debt": self.total_debt,
            "net_worth": self.net_worth,
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
            total_income=float(data["total_income"]),
            total_expenses=float(data["total_expenses"]),
            net_cash_flow=float(data["net_cash_flow"]),
            total_account_balance=float(
                data["total_account_balance"]
            ),
            total_goal_progress=float(
                data["total_goal_progress"]
            ),
            total_debt=float(
                data["total_debt"]
            ),
            net_worth=float(
                data["net_worth"]
            ),
            health_score=int(
                data["health_score"]
            ),
            health_status=data["health_status"],
        )