from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.transaction_dependencies import get_transaction_service
from app.dependencies.user_dependencies import get_current_user
from app.entities.user import User
from app.schemas.base_schemas import SearchResponse
from app.schemas.transaction_schemas import (
    TransactionCreate,
    TransactionResponse,
    TransactionSearch,
    TransactionUpdate,
    TransferResponse,
    TransferTransactionCreate,
)
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.get("", response_model=SearchResponse[TransactionResponse])
def search_transactions(
    search: TransactionSearch = Depends(),
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[TransactionResponse]:
    """
    Search transactions by account, category, type, currency, date range, amount range,
    and source for the authenticated user.
    """
    return service.search(cast(UUID, current_user.id), search)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    """Retrieve a specific transaction owned by the current user."""
    return service.get(transaction_id, cast(UUID, current_user.id))


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
    """Create a transaction and optionally link or create tags automatically."""
    return service.create_transaction(
        transaction_data,
        user_id=cast(UUID, current_user.id),
    )


@router.post(
    "/transfer",
    response_model=TransferResponse,
    summary="Create a new transfer transaction",
    description=(
        "Create a new transfer transaction with the provided data. "
        "Requires a valid JWT token in the Authorization header."
    ),
)
async def create_transfer_transaction(
    transaction_data: TransferTransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> TransferResponse:
    """Create a transfer transaction between two owned accounts."""
    return service.create_transfer_transaction(
        transaction_data, user_id=cast(UUID, current_user.id)
    )


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
    """Update a transaction owned by the current user."""
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
    """Delete a transaction owned by the current user."""
    service.delete(transaction_id, user_id=cast(UUID, current_user.id))
    return None
