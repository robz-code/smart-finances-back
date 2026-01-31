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
    ReportingParameters,
)
from app.services.reporting_service import ReportingService

router = APIRouter()


@router.get(
    "/categories-summary", response_model=SearchResponse[CategorySummaryResponse]
)
def get_categories_summary(
    parameters: ReportingParameters = Depends(),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[CategorySummaryResponse]:
    """
    Get categories with their transaction amounts for a specified period or date range.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`

    Date range: Provide EITHER `period` OR both `date_from` and `date_to`.
    If `period` is set, date filters are ignored.

    Query parameters:
    - `period` (optional): Time period for aggregation. Options: `day`, `week`, `month`, `year`
    - `date_from` (optional): Start date (use with `date_to`, ignored when `period` is set)
    - `date_to` (optional): End date (use with `date_from`, ignored when `period` is set)
    - `type` (optional): Filter categories by type (`income` or `expense`)
    - `category_id` (optional): Filter to a single category
    - `account_id` (optional): Filter transactions by account
    - `transaction_type` (optional): Filter transactions by type (`income` or `expense`)
    - `currency` (optional): Filter by currency
    - `amount_min` (optional): Minimum transaction amount
    - `amount_max` (optional): Maximum transaction amount
    - `source` (optional): Filter by transaction source

    Returns categories with a `transaction_amount` field containing the net-signed sum
    (income adds, expense subtracts) for the specified period.
    """
    user_id = cast(UUID, current_user.id)
    return service.get_categories_summary(
        user_id=user_id, parameters=parameters
    )
