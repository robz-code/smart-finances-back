from typing import List, cast
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies.installment_dependencies import get_installment_service
from app.dependencies.user_dependencies import get_current_user
from app.entities.user import User
from app.schemas.installment_schemas import (
    InstallmentBase,
    InstallmentUpdate,
)
from app.services.installment_service import InstallmentService

router = APIRouter()


@router.get("/transaction/{transaction_id}", response_model=List[InstallmentBase])
def get_installments_by_transaction(
    transaction_id: UUID,
    service: InstallmentService = Depends(get_installment_service),
    current_user: User = Depends(get_current_user),
) -> List[InstallmentBase]:
    return service.get_by_transaction_id(transaction_id, cast(UUID, current_user.id))


@router.put("/{installment_id}", response_model=InstallmentBase)
def update_installment(
    installment_id: UUID,
    payload: InstallmentUpdate,
    service: InstallmentService = Depends(get_installment_service),
    current_user: User = Depends(get_current_user),
) -> InstallmentBase:
    return service.update_installment(
        installment_id, payload, cast(UUID, current_user.id)
    )
