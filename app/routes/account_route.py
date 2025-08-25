from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.account_dependencies import get_account_service
from app.dependencies.user_dependencies import get_current_user
from app.entities.user import User
from app.schemas.account_schemas import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
)
from app.schemas.base_schemas import SearchResponse
from app.services.account_service import AccountService

router = APIRouter()


@router.get("", response_model=SearchResponse[AccountResponse])
def read_accounts_list(
    service: AccountService = Depends(get_account_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[AccountResponse]:
    """
    Get a list of all accounts.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get_by_user_id(cast(UUID, current_user.id))


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    dependencies=[Depends(get_current_user)],
)
def read_account(
    account_id: UUID, service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """
    Get a specific account by ID.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get(account_id)


@router.post(
    "",
    response_model=AccountResponse,
    summary="Create a new account",
    description=(
        "Create a new account with the provided data. Requires a valid JWT "
        "token in the Authorization header."
    ),
)
async def create_account(
    account_data: AccountCreate,
    service: AccountService = Depends(get_account_service),
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    """
    Create a new account.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.add(account_data.to_model(cast(UUID, current_user.id)))


@router.put(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Update an account",
    description=(
        "Update an account with the provided data. Requires a valid JWT token "
        "in the Authorization header."
    ),
)
async def update_account(
    account_id: UUID,
    account_data: AccountUpdate,
    service: AccountService = Depends(get_account_service),
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    """
    Update an account.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.update(
        account_id,
        account_data,
        user_id=cast(UUID, current_user.id),
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    service: AccountService = Depends(get_account_service),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete an account.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    service.delete(account_id, user_id=cast(UUID, current_user.id))
    return None
