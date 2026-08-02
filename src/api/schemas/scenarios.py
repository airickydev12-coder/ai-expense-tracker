"""API schemas for financial scenario endpoints."""

from typing import Any

from pydantic import BaseModel, Field

from src.financial.scenarios.models import ScenarioType
from src.financial.scenarios.ranking import ScenarioRankingMetric


class ScenarioRunRequest(BaseModel):
    """Request body for running or saving one financial scenario."""

    scenario_type: ScenarioType
    name: str = Field(min_length=1)
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


class ScenarioOptimizeRequest(BaseModel):
    """Request body for running the scenario optimizer."""

    limit: int | None = Field(default=None, gt=0)
    ranking_metric: ScenarioRankingMetric = ScenarioRankingMetric.OVERALL
    horizon_months: int = Field(default=12, gt=0)


class ScenarioCombinedRequest(BaseModel):
    """Request body for running a combined, multi-step scenario plan."""

    name: str = Field(min_length=1)
    description: str = ""
    requests: list[ScenarioRunRequest] = Field(min_length=1)


class ScenarioParseRequest(BaseModel):
    """Request body for parsing free text into a scenario draft."""

    text: str = Field(min_length=1)
