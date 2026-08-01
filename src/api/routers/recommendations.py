"""API routes for financial recommendations."""

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas.recommendations import (
    RecommendationCategoryFilter,
    RecommendationCategoryResponse,
    RecommendationPriorityFilter,
    RecommendationPriorityResponse,
    RecommendationResponse,
)
from src.financial.application.recommendation_application_service import (
    build_recommendations,
    get_recommendation_by_key,
)
from src.financial.recommendations.category import (
    RecommendationCategory,
)
from src.financial.recommendations.priority import (
    RecommendationPriority,
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
    priority: RecommendationPriorityFilter | None = Query(
        default=None,
        description="Return recommendations with this priority.",
    ),
    category: RecommendationCategoryFilter | None = Query(
        default=None,
        description="Return recommendations in this category.",
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        description="Maximum number of filtered recommendations to return.",
    ),
) -> list[RecommendationResponse]:
    """Return prioritized and optionally filtered recommendations."""

    recommendations = build_recommendations(
        priority=priority.value if priority is not None else None,
        category=category.value if category is not None else None,
        limit=limit,
    )

    return [
        RecommendationResponse.model_validate(recommendation.to_dict())
        for recommendation in recommendations
    ]


@router.get(
    "/categories",
    response_model=list[RecommendationCategoryResponse],
)
def get_recommendation_categories() -> list[RecommendationCategoryResponse]:
    """Return supported recommendation categories."""

    return [
        RecommendationCategoryResponse(
            name=category.name,
            value=category.value,
        )
        for category in RecommendationCategory
    ]


@router.get(
    "/priorities",
    response_model=list[RecommendationPriorityResponse],
)
def get_recommendation_priorities() -> list[RecommendationPriorityResponse]:
    """Return supported recommendation priorities."""

    return [
        RecommendationPriorityResponse(
            name=priority.name,
            value=priority.value,
            score=priority.value * 100,
        )
        for priority in RecommendationPriority
    ]


@router.get(
    "/{recommendation_key}",
    response_model=RecommendationResponse,
)
def get_recommendation(
    recommendation_key: str,
) -> RecommendationResponse:
    """Return a single recommendation by key."""

    recommendation = get_recommendation_by_key(
        recommendation_key,
    )

    if recommendation is None:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found.",
        )

    return RecommendationResponse.model_validate(recommendation.to_dict())
