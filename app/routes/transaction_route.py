from datetime import date
from decimal import Decimal
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.transaction_dependencies import get_transaction_service
from app.dependencies.user_dependencies import get_current_user
from app.entities.user import User
from app.schemas.transaction_schemas import (
    TransactionCreate,
    TransactionResponse,
    TransactionSearch,
    TransactionUpdate,
)
from app.schemas.base_schemas import SearchResponse
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.get("", response_model=SearchResponse[TransactionResponse])
def search_transactions(
    account_id: UUID = Query(None, description="Filter by account ID"),
    category_id: UUID = Query(None, description="Filter by category ID"),
    group_id: UUID = Query(None, description="Filter by group ID"),
    type: str = Query(None, description="Filter by transaction type"),
    currency: str = Query(None, description="Filter by currency"),
    date_from: date = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    date_to: date = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    amount_min: Decimal = Query(None, description="Filter by minimum amount"),
    amount_max: Decimal = Query(None, description="Filter by maximum amount"),
    source: str = Query(None, description="Filter by source"),
    has_installments: bool = Query(None, description="Filter by installments flag"),
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[TransactionResponse]:
    """
    Search transactions with various filters.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    search_params = TransactionSearch(
        account_id=account_id,
        category_id=category_id,
        group_id=group_id,
        type=type,
        currency=currency,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        source=source,
        has_installments=has_installments,
    )
    return service.search(cast(UUID, current_user.id), search_params)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    """
    Get a specific transaction by ID.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get(transaction_id)


@router.post(
    "",
    response_model=TransactionResponse,
    summary="Create a new transaction",
    description=(
        "Create a new transaction with the provided data. Requires a valid JWT "
        "token in the Authorization header."
    ),
)
async def create_transaction(
    transaction_data: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    """
    Create a new transaction.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.add(transaction_data.to_model(cast(UUID, current_user.id)))


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update a transaction",
    description=(
        "Update a transaction with the provided data. Requires a valid JWT token "
        "in the Authorization header."
    ),
)
async def update_transaction(
    transaction_id: UUID,
    transaction_data: TransactionUpdate,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    """
    Update a transaction.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.update(
        transaction_id,
        transaction_data,
        user_id=cast(UUID, current_user.id),
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a transaction.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    service.delete(transaction_id, user_id=cast(UUID, current_user.id))
    return None


# Additional convenience endpoints
@router.get("/account/{account_id}", response_model=SearchResponse[TransactionResponse])
def get_transactions_by_account(
    account_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[TransactionResponse]:
    """
    Get all transactions for a specific account.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get_by_account_id(cast(UUID, current_user.id), account_id)


@router.get("/category/{category_id}", response_model=SearchResponse[TransactionResponse])
def get_transactions_by_category(
    category_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[TransactionResponse]:
    """
    Get all transactions for a specific category.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get_by_category_id(cast(UUID, current_user.id), category_id)


@router.get("/group/{group_id}", response_model=SearchResponse[TransactionResponse])
def get_transactions_by_group(
    group_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[TransactionResponse]:
    """
    Get all transactions for a specific group.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get_by_group_id(cast(UUID, current_user.id), group_id)
