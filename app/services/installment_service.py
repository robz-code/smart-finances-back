from __future__ import annotations

import logging
from typing import List, Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.installment import Installment
from app.entities.transaction import Transaction
from app.repository.installment_repository import InstallmentRepository
from app.schemas.installment_schemas import InstallmentCreate, InstallmentUpdate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class InstallmentService(BaseService[Installment]):
    def __init__(self, db: Session):
        repository = InstallmentRepository(db)
        super().__init__(db, repository, Installment)

    def create_for_transaction(
        self, transaction: Transaction, installments: Sequence[InstallmentCreate]
    ) -> List[Installment]:
        if not installments:
            return []

        entities: List[Installment] = []
        for index, installment in enumerate(installments, start=1):
            entities.append(
                Installment(
                    transaction_id=transaction.id,
                    due_date=installment.due_date,
                    amount=installment.amount,
                    installment_number=index,
                )
            )

        return self.repository.create_many(entities)

    def get_by_transaction_id(
        self, transaction_id: UUID, user_id: UUID
    ) -> List[Installment]:
        transaction = self._get_owned_transaction(transaction_id, user_id)
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")

        return self.repository.get_by_transaction_id(transaction_id)

    def update_installment(
        self, installment_id: UUID, payload: InstallmentUpdate, user_id: UUID
    ) -> Installment:
        installment = self.get(installment_id)

        transaction = self._get_owned_transaction(installment.transaction_id, user_id)
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return installment

        updated = self.repository.update_fields(installment_id, update_data)
        if updated is None:
            raise HTTPException(status_code=404, detail="Installment not found")

        return updated

    def delete_by_transaction_id(self, transaction_id: UUID) -> None:
        self.repository.delete_by_transaction_id(transaction_id)

    def _get_owned_transaction(
        self, transaction_id: UUID, user_id: UUID
    ) -> Transaction | None:
        transaction = (
            self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
        )
        if transaction is None:
            return None
        if transaction.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Access denied to this transaction"
            )

        return transaction
