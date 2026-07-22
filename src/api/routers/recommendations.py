"""API routes for financial recommendations."""

from fastapi import APIRouter, Query

from src.api.schemas.recommendations import RecommendationResponse
from src.financial.application.recommendation_application_service import (
    build_recommendations,
)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.get(
    "",
    response_model=list[RecommendationResponse],
)
def get_recommendations(
    limit: int | None = Query(
        default=None,
        ge=1,
        description="Maximum number of recommendations to return.",
    ),
) -> list[RecommendationResponse]:
    """Return prioritized financial recommendations."""

    recommendations = build_recommendations(limit=limit)

    return [
        RecommendationResponse.model_validate(recommendation.to_dict())
        for recommendation in recommendations
    ]
