from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.budget_dependencies import get_budget_service
from app.dependencies.user_dependencies import get_current_user
from app.entities.user import User
from app.schemas.base_schemas import SearchResponse
from app.schemas.budget_schemas import (
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
)
from app.services.budget_service import BudgetService

router = APIRouter()


@router.get("", response_model=SearchResponse[BudgetResponse])
def read_budgets_list(
    service: BudgetService = Depends(get_budget_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[BudgetResponse]:
    """
    Get a list of all budgets.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get_by_user_id(cast(UUID, current_user.id))


@router.get(
    "/{budget_id}",
    response_model=BudgetResponse,
    dependencies=[Depends(get_current_user)],
)
def read_budget(
    budget_id: UUID, service: BudgetService = Depends(get_budget_service)
) -> BudgetResponse:
    """
    Get a specific budget by ID.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get(budget_id)


@router.post(
    "",
    response_model=BudgetResponse,
    summary="Create a new budget",
    description=(
        "Create a new budget with the provided data. Requires a valid JWT "
        "token in the Authorization header."
    ),
)
async def create_budget(
    budget_data: BudgetCreate,
    service: BudgetService = Depends(get_budget_service),
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    """
    Create a new budget.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.add(budget_data.to_model(cast(UUID, current_user.id)))


@router.put(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Update a budget",
    description=(
        "Update a budget with the provided data. Requires a valid JWT token "
        "in the Authorization header."
    ),
)
async def update_budget(
    budget_id: UUID,
    budget_data: BudgetUpdate,
    service: BudgetService = Depends(get_budget_service),
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    """
    Update a budget.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.update(
        budget_id,
        budget_data,
        user_id=cast(UUID, current_user.id),
    )


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: UUID,
    service: BudgetService = Depends(get_budget_service),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a budget.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    service.delete(budget_id, user_id=cast(UUID, current_user.id))
    return None
