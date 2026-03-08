import logging
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.entities.account import Account
from app.entities.category import Category
from app.entities.transaction import Transaction
from app.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Category)

    def count_transactions(self, category_id: UUID) -> int:
        """Return the number of visible transactions that belong to this category.

        Excludes transactions from soft-deleted accounts, consistent with the
        soft-delete strategy where those transactions are invisible to the user.
        """
        logger.debug(f"DB count_transactions: category_id={category_id}")
        return (
            self.db.query(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .filter(
                Transaction.category_id == category_id,
                Account.is_deleted == False,  # noqa: E712
            )
            .count()
        )

    def migrate_transactions(self, source_id: UUID, target_id: UUID) -> int:
        """
        Reassign all transactions from source_category to target_category.

        Returns the number of rows updated.
        """
        logger.debug(
            f"DB migrate_transactions: source={source_id} → target={target_id}"
        )
        updated = (
            self.db.query(Transaction)
            .filter(Transaction.category_id == source_id)
            .update({"category_id": target_id}, synchronize_session=False)
        )
        self.db.commit()
        logger.info(
            f"Migrated {updated} transaction(s) from category {source_id} → {target_id}"
        )
        return updated

    def get_transfer_category(self, user_id: UUID) -> Category:
        return (
            self.db.query(self.model)
            .filter(self.model.user_id == user_id, self.model.name == "transfer")
            .first()
        )

    def get_by_user_id_and_type(
        self, user_id: UUID, category_type: str
    ) -> List[Category]:
        return (
            self.db.query(self.model)
            .filter(self.model.user_id == user_id, self.model.type == category_type)
            .all()
        )
