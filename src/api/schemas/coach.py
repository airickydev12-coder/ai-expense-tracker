"""API schemas for AI financial coach endpoints."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CoachNarrativeResponse(BaseModel):
    """Response body containing the AI-generated financial snapshot narrative."""

    narrative: str


class RecommendationEvidenceResponse(BaseModel):
    """Real, precomputed evidence grounding a recommendation explanation."""

    type: Literal["debt", "aggregate"]
    debt_name: str | None = None
    debt_balance: Decimal | None = None
    interest_rate: float | None = None
    minimum_payment: Decimal | None = None
    extra_monthly_payment: float | None = None
    payoff_months_saved: int | None = None
    total_interest_saved: Decimal | None = None
    total_debt: Decimal
    total_income: Decimal | None = None
    debt_to_income_ratio: float | None = None
    total_account_balance: Decimal | None = None
    total_goal_progress: Decimal | None = None


class RecommendationExplanationResponse(BaseModel):
    """Structured, evidence-grounded explanation for one recommendation."""

    recommendation_key: str
    reason: str
    evidence: RecommendationEvidenceResponse
    expected_impact: str
    confidence: Literal["Low", "Medium", "High"]
    assumptions: list[str]


class MonthlyReviewIncomeExpensesResponse(BaseModel):
    """Income-versus-expenses section of a monthly review."""

    narrative: str
    income_change: Decimal
    expense_change: Decimal


class MonthlyReviewCashFlowResponse(BaseModel):
    """Cash-flow section of a monthly review."""

    narrative: str
    change: Decimal
    direction: str


class MonthlyReviewDebtProgressResponse(BaseModel):
    """Debt-progress section of a monthly review."""

    narrative: str
    total_debt: Decimal


class MonthlyReviewSavingsProgressResponse(BaseModel):
    """Savings-progress section of a monthly review."""

    narrative: str


class MonthlyReviewGoalStatusResponse(BaseModel):
    """Goal-status section of a monthly review."""

    narrative: str


class MonthlyReviewHealthScoreResponse(BaseModel):
    """Health-score section of a monthly review."""

    narrative: str
    change: Decimal
    direction: str
    current_score: int


class MonthlyReviewNextActionResponse(BaseModel):
    """One top-priority recommended action surfaced in a monthly review."""

    key: str
    title: str
    message: str
    action: str
    priority: str


class MonthlyReviewCategoryTrendResponse(BaseModel):
    """One notable category-level spending change surfaced in a monthly review."""

    category: str
    change: Decimal
    direction: str


class MonthlyReviewResponse(BaseModel):
    """
    Response body for a monthly financial review.

    `status` discriminates between a full review ("ok") and the two
    graceful-degradation cases where there isn't enough recorded history
    yet -- only `message` (and `last_recorded_snapshot`, when available)
    are populated in those cases. `generated_at` is only set when the
    review was saved (via POST) -- a GET preview is never persisted.
    """

    status: Literal["ok", "no_history", "insufficient_recent_history"]
    message: str | None = None
    last_recorded_snapshot: str | None = None
    generated_at: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    overall_summary: str | None = None
    income_vs_expenses: MonthlyReviewIncomeExpensesResponse | None = None
    cash_flow: MonthlyReviewCashFlowResponse | None = None
    debt_progress: MonthlyReviewDebtProgressResponse | None = None
    savings_progress: MonthlyReviewSavingsProgressResponse | None = None
    goal_status: MonthlyReviewGoalStatusResponse | None = None
    health_score: MonthlyReviewHealthScoreResponse | None = None
    top_actions: list[MonthlyReviewNextActionResponse] | None = None
    category_trends: list[MonthlyReviewCategoryTrendResponse] | None = None
    known_gaps: list[str] | None = None


class CoachChatMessage(BaseModel):
    """One message in an AI coach chat conversation."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class CoachChatRequest(BaseModel):
    """Request body for sending a message to the AI financial coach chat.

    Carries the full conversation history, including the newest user
    message — the frontend keeps history in React state only and resends
    it every call (stateless backend, per the ephemeral-chat design).
    """

    messages: list[CoachChatMessage] = Field(min_length=1)


class CoachChatResponse(BaseModel):
    """Response body containing the assistant's reply for this turn."""

    reply: str
