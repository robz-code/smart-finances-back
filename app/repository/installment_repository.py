import logging
from typing import Iterable, List, Optional
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.entities.installment import Installment
from app.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class InstallmentRepository(BaseRepository[Installment]):
    def __init__(self, db: Session):
        super().__init__(db, Installment)

    def create_many(self, installments: Iterable[Installment]) -> List[Installment]:
        """Persist a collection of installments in a single transaction."""

        installments_list = list(installments)
        if not installments_list:
            return []

        try:
            self.db.add_all(installments_list)
            self.db.commit()
            for installment in installments_list:
                self.db.refresh(installment)
            logger.info(
                "Successfully created %s installments for transaction %s",
                len(installments_list),
                installments_list[0].transaction_id,
            )
            return installments_list
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Error creating installments: %s", exc)
            raise

    def get_by_transaction_id(self, transaction_id: UUID) -> List[Installment]:
        return (
            self.db.query(Installment)
            .filter(Installment.transaction_id == transaction_id)
            .order_by(Installment.installment_number.asc())
            .all()
        )

    def delete_by_transaction_id(self, transaction_id: UUID) -> int:
        try:
            deleted = (
                self.db.query(Installment)
                .filter(Installment.transaction_id == transaction_id)
                .delete(synchronize_session=False)
            )
            if deleted:
                logger.info(
                    "Deleted %s installments for transaction %s",
                    deleted,
                    transaction_id,
                )
            self.db.commit()
            return deleted
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error(
                "Error deleting installments for transaction %s: %s",
                transaction_id,
                exc,
            )
            raise

    def update_fields(
        self, installment_id: UUID, data: dict[str, object]
    ) -> Optional[Installment]:
        installment = self.get(installment_id)
        if installment is None:
            return None

        try:
            for key, value in data.items():
                if value is not None and hasattr(installment, key):
                    setattr(installment, key, value)

            self.db.commit()
            self.db.refresh(installment)
            logger.info("Updated installment %s", installment_id)
            return installment
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Error updating installment %s: %s", installment_id, exc)
            raise
