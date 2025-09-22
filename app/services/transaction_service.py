import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.group import Group
from app.entities.group_member import GroupMember
from app.entities.transaction import Transaction
from app.repository.transaction_repository import TransactionRepository
from app.schemas.base_schemas import SearchResponse
from app.schemas.transaction_schemas import TransactionSearch
from app.services.account_service import AccountService
from app.services.base_service import BaseService
from app.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class TransactionService(BaseService[Transaction]):
    def __init__(self, db: Session):
        repository = TransactionRepository(db)
        super().__init__(db, repository, Transaction)
        self.account_service = AccountService(db)
        self.category_service = CategoryService(db)

    def get(self, transaction_id: UUID, user_id: UUID) -> Transaction:
        """Retrieve a transaction ensuring it belongs to the requesting user."""

        transaction = super().get(transaction_id)
        if transaction.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Access denied to this transaction"
            )

        return transaction

    def search(
        self, user_id: UUID, search_params: TransactionSearch
    ) -> SearchResponse[Transaction]:
        """Search transactions with validation and error handling"""
        try:
            result = self.repository.search(user_id, search_params)
            return SearchResponse(total=len(result), results=result)
        except Exception as e:
            logger.error(f"Error searching transactions: {str(e)}")
            raise HTTPException(status_code=500, detail="Error searching transactions")

    def get_by_account_id(
        self, user_id: UUID, account_id: UUID
    ) -> SearchResponse[Transaction]:
        """Get transactions by account ID with validation"""
        try:
            result = self.repository.get_by_account_id(user_id, account_id)
            return SearchResponse(total=len(result), results=result)
        except Exception as e:
            logger.error(f"Error getting transactions by account: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving transactions")

    def get_by_category_id(
        self, user_id: UUID, category_id: UUID
    ) -> SearchResponse[Transaction]:
        """Get transactions by category ID with validation"""
        try:
            result = self.repository.get_by_category_id(user_id, category_id)
            return SearchResponse(total=len(result), results=result)
        except Exception as e:
            logger.error(f"Error getting transactions by category: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving transactions")

    def get_by_group_id(
        self, user_id: UUID, group_id: UUID
    ) -> SearchResponse[Transaction]:
        """Get transactions by group ID with validation"""
        try:
            result = self.repository.get_by_group_id(user_id, group_id)
            return SearchResponse(total=len(result), results=result)
        except Exception as e:
            logger.error(f"Error getting transactions by group: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving transactions")

    def get_by_date_range(
        self, user_id: UUID, date_from: str, date_to: str
    ) -> SearchResponse[Transaction]:
        """Get transactions by date range with validation"""
        try:
            result = self.repository.get_by_date_range(user_id, date_from, date_to)
            return SearchResponse(total=len(result), results=result)
        except Exception as e:
            logger.error(f"Error getting transactions by date range: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving transactions")

    def before_create(self, obj_in: Transaction, **kwargs: Any) -> bool:
        """Validate transaction before creation"""
        # Validate amount is not zero before any other business rules
        if obj_in.amount == 0:
            raise HTTPException(
                status_code=400, detail="Transaction amount cannot be zero"
            )

        # Ensure that a category is provided
        if obj_in.category_id is None:
            raise HTTPException(
                status_code=400, detail="Category is required for transactions"
            )

        # Validate that the user owns the account
        if not self._validate_account_ownership(obj_in.user_id, obj_in.account_id):
            raise HTTPException(
                status_code=403, detail="Account not found or access denied"
            )

        # Validate that the user owns the category
        if not self._validate_category_ownership(obj_in.user_id, obj_in.category_id):
            raise HTTPException(
                status_code=403, detail="Category not found or access denied"
            )

        # Validate that the user owns the group if provided
        if obj_in.group_id and not self._validate_group_ownership(
            obj_in.user_id, obj_in.group_id
        ):
            raise HTTPException(
                status_code=403, detail="Group not found or access denied"
            )

        return True

    def before_update(self, id: UUID, obj_in: Any, **kwargs: Any) -> bool:
        """Validate transaction before update"""
        # Get the existing transaction
        existing_transaction = self.repository.get(id)
        if not existing_transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Validate that the user owns the transaction
        user_id = kwargs.get("user_id")
        if user_id and existing_transaction.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Access denied to this transaction"
            )

        # Determine if the payload explicitly contains account/category updates
        payload: dict[str, Any] = {}
        model_dump = getattr(obj_in, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump(exclude_unset=True)
            if isinstance(dumped, dict):
                payload = dumped

        # Validate account ownership if account_id is being updated
        account_id = (
            payload.get("account_id")
            if payload
            else getattr(obj_in, "account_id", None)
        )
        if account_id is not None and not self._validate_account_ownership(
            user_id, account_id
        ):
            raise HTTPException(
                status_code=403, detail="Account not found or access denied"
            )

        # Validate category ownership if category_id is being updated
        category_provided = False
        if payload:
            category_provided = "category_id" in payload
            category_id = payload.get("category_id")
        else:
            category_id = getattr(obj_in, "category_id", None)
            category_provided = category_id is not None

        if category_provided:
            if category_id is None:
                raise HTTPException(
                    status_code=400, detail="Category is required for transactions"
                )
            if not self._validate_category_ownership(user_id, category_id):
                raise HTTPException(
                    status_code=403, detail="Category not found or access denied"
                )

        # Validate group ownership if group_id is being updated
        group_id = (
            payload.get("group_id") if payload else getattr(obj_in, "group_id", None)
        )
        if group_id and not self._validate_group_ownership(user_id, group_id):
            raise HTTPException(
                status_code=403, detail="Group not found or access denied"
            )

        return True

    def before_delete(self, id: UUID, **kwargs: Any) -> Transaction:
        """Validate transaction before deletion"""
        # Get the existing transaction
        existing_transaction = self.repository.get(id)
        if not existing_transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Validate that the user owns the transaction
        user_id = kwargs.get("user_id")
        if user_id and existing_transaction.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Access denied to this transaction"
            )

        return existing_transaction

    def _validate_account_ownership(self, user_id: UUID, account_id: UUID) -> bool:
        """Validate that the user owns the account"""
        try:
            account = self.account_service.get(account_id)
        except HTTPException:
            return False
        except Exception:
            return False

        return bool(account and account.user_id == user_id)

    def _validate_category_ownership(self, user_id: UUID, category_id: UUID) -> bool:
        """Validate that the user owns the category"""
        try:
            category = self.category_service.get(category_id)
        except HTTPException:
            return False
        except Exception:
            return False

        return bool(category and category.user_id == user_id)

    def _validate_group_ownership(self, user_id: UUID, group_id: UUID) -> bool:
        """Validate that the user owns the group or is a member of it."""

        try:
            group = self.db.query(Group).filter(Group.id == group_id).first()
            if group is None:
                return False

            if getattr(group, "created_by", None) == user_id:
                return True

            membership = (
                self.db.query(GroupMember)
                .filter(
                    GroupMember.group_id == group_id,
                    GroupMember.user_id == user_id,
                )
                .first()
            )
            return membership is not None
        except Exception as exc:
            logger.warning(
                "Error validating group ownership for user %s and group %s: %s",
                user_id,
                group_id,
                exc,
            )
            return False
