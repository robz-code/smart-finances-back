from typing import Optional, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies.reporting_dependencies import get_reporting_service
from app.dependencies.user_dependencies import get_current_user
from app.entities.category import CategoryType
from app.entities.user import User
from app.schemas.base_schemas import SearchResponse
from app.schemas.reporting_schemas import (
    CategorySummaryResponse,
    TransactionSummaryPeriod,
)
from app.services.reporting_service import ReportingService

router = APIRouter()


@router.get(
    "/categories-summary", response_model=SearchResponse[CategorySummaryResponse]
)
def get_categories_summary(
    period: TransactionSummaryPeriod = Query(..., alias="period"),
    category_type: Optional[CategoryType] = Query(default=None, alias="type"),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[CategorySummaryResponse]:
    """
    Get categories with their transaction amounts for a specified period.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`

    Query parameters:
    - `period` (required): Time period for aggregation. Options: `day`, `week`, `month`, `year`
    - `type` (optional): Filter categories by type (`income` or `expense`).

    Returns categories with a `transaction_amount` field containing the net-signed sum
    (income adds, expense subtracts) for the specified period.
    """
    user_id = cast(UUID, current_user.id)
    return service.get_categories_summary(
        user_id=user_id, period=period, category_type=category_type
    )
