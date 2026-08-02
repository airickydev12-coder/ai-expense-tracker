"""API schemas for financial history endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FinancialSnapshotResponse(BaseModel):
    """Serialized representation of a historical financial snapshot."""

    model_config = ConfigDict(from_attributes=True)

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
