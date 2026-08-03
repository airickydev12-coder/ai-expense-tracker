"""API routes for financial recommendations."""

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_current_user
from src.api.schemas.recommendations import (
    RecommendationActionRequest,
    RecommendationCategoryResponse,
    RecommendationPriorityFilter,
    RecommendationPriorityResponse,
    RecommendationRecordResponse,
    RecommendationResponse,
)
from src.financial.application.recommendation_application_service import (
    build_recommendations,
    get_recommendation_by_key,
)
from src.financial.recommendations.category import (
    RecommendationCategory,
)
from src.financial.recommendations.history import RecommendationRecord
from src.financial.recommendations.history_service import (
    complete_recommendation,
    dismiss_recommendation,
    suppress_recommendation,
)
from src.financial.recommendations.priority import (
    RecommendationPriority,
)
from src.financial.users.models import User

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
    category: RecommendationCategory | None = Query(
        default=None,
        description="Return recommendations in this category.",
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        description="Maximum number of filtered recommendations to return.",
    ),
    current_user: User = Depends(get_current_user),
) -> list[RecommendationResponse]:
    """Return prioritized and optionally filtered recommendations."""

    recommendations = build_recommendations(
        current_user.id,
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
    current_user: User = Depends(get_current_user),
) -> RecommendationResponse:
    """Return a single recommendation by key."""

    recommendation = get_recommendation_by_key(
        current_user.id,
        recommendation_key,
    )

    if recommendation is None:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found.",
        )

    return RecommendationResponse.model_validate(recommendation.to_dict())


def _apply_lifecycle_action(
    action: Callable[..., RecommendationRecord | None],
    user_id: int,
    recommendation_key: str,
    request: RecommendationActionRequest,
) -> RecommendationRecordResponse:
    """Apply a lifecycle action and return its resulting record, or 404."""

    record = action(user_id, recommendation_key, note=request.note)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No lifecycle record found for this recommendation. "
                "Fetch GET /recommendations first to register it."
            ),
        )

    return RecommendationRecordResponse.model_validate(record.to_dict())


@router.post(
    "/{recommendation_key}/dismiss",
    response_model=RecommendationRecordResponse,
)
def dismiss_recommendation_route(
    recommendation_key: str,
    request: RecommendationActionRequest = RecommendationActionRequest(),
    current_user: User = Depends(get_current_user),
) -> RecommendationRecordResponse:
    """Mark a recommendation as dismissed."""

    return _apply_lifecycle_action(
        dismiss_recommendation,
        current_user.id,
        recommendation_key,
        request,
    )


@router.post(
    "/{recommendation_key}/complete",
    response_model=RecommendationRecordResponse,
)
def complete_recommendation_route(
    recommendation_key: str,
    request: RecommendationActionRequest = RecommendationActionRequest(),
    current_user: User = Depends(get_current_user),
) -> RecommendationRecordResponse:
    """Mark a recommendation as completed."""

    return _apply_lifecycle_action(
        complete_recommendation,
        current_user.id,
        recommendation_key,
        request,
    )


@router.post(
    "/{recommendation_key}/suppress",
    response_model=RecommendationRecordResponse,
)
def suppress_recommendation_route(
    recommendation_key: str,
    request: RecommendationActionRequest = RecommendationActionRequest(),
    current_user: User = Depends(get_current_user),
) -> RecommendationRecordResponse:
    """Mark a recommendation as suppressed."""

    return _apply_lifecycle_action(
        suppress_recommendation,
        current_user.id,
        recommendation_key,
        request,
    )
