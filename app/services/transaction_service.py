import logging
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.entities.group import Group
from app.entities.tags import Tag
from app.entities.transaction import Transaction, TransactionType
from app.entities.transaction_tag import TransactionTag
from app.repository.transaction_repository import TransactionRepository
from app.schemas.base_schemas import SearchResponse
from app.schemas.category_schemas import CategoryResponseBase
from app.schemas.installment_schemas import InstallmentBase
from app.schemas.tag_schemas import TagTransactionCreate
from app.schemas.transaction_schemas import (
    TransactionCreate,
    TransactionRelatedEntity,
    TransactionResponse,
    TransactionSearch,
    TransferResponse,
    TransferTransactionCreate,
)
from app.services.account_service import AccountService
from app.services.base_service import BaseService
from app.services.category_service import CategoryService
from app.services.group_service import GroupService
from app.services.installment_service import InstallmentService
from app.services.tag_service import TagService

logger = logging.getLogger(__name__)


class TransactionService(BaseService[Transaction]):
    def __init__(self, db: Session):
        repository = TransactionRepository(db)
        super().__init__(db, repository, Transaction)
        self.account_service = AccountService(db)
        self.category_service = CategoryService(db)
        self.group_service = GroupService(db)
        self.installment_service = InstallmentService(db)
        self.tag_service = TagService(db)

    def get(self, transaction_id: UUID, user_id: UUID) -> TransactionResponse:
        """Retrieve a transaction ensuring it belongs to the requesting user."""

        transaction = super().get(transaction_id)
        if transaction.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Access denied to this transaction"
            )

        return self._build_transaction_response(transaction)

    def search(
        self, user_id: UUID, search_params: TransactionSearch
    ) -> SearchResponse[TransactionResponse]:
        """Search transactions with validation and error handling"""
        try:
            result = self.repository.search(user_id, search_params)
            return self._build_search_response(result)
        except Exception as e:
            logger.error(f"Error searching transactions: {str(e)}")
            raise HTTPException(status_code=500, detail="Error searching transactions")

    def get_by_account_id(
        self, user_id: UUID, account_id: UUID
    ) -> SearchResponse[TransactionResponse]:
        """Get transactions by account ID with validation"""
        try:
            result = self.repository.get_by_account_id(user_id, account_id)
            return self._build_search_response(result)
        except Exception as e:
            logger.error(f"Error getting transactions by account: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving transactions")

    def get_by_category_id(
        self, user_id: UUID, category_id: UUID
    ) -> SearchResponse[TransactionResponse]:
        """Get transactions by category ID with validation"""
        try:
            result = self.repository.get_by_category_id(user_id, category_id)
            return self._build_search_response(result)
        except Exception as e:
            logger.error(f"Error getting transactions by category: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving transactions")

    def get_by_group_id(
        self, user_id: UUID, group_id: UUID
    ) -> SearchResponse[TransactionResponse]:
        """Get transactions by group ID with validation"""
        try:
            result = self.repository.get_by_group_id(user_id, group_id)
            return self._build_search_response(result)
        except Exception as e:
            logger.error(f"Error getting transactions by group: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving transactions")

    def get_by_date_range(
        self, user_id: UUID, date_from: str, date_to: str
    ) -> SearchResponse[TransactionResponse]:
        """Get transactions by date range with validation"""
        try:
            result = self.repository.get_by_date_range(user_id, date_from, date_to)
            return self._build_search_response(result)
        except Exception as e:
            logger.error(f"Error getting transactions by date range: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving transactions")

    def create_transaction(
        self, payload: TransactionCreate, *, user_id: UUID
    ) -> TransactionResponse:
        """Create a transaction from a payload, handling tag linkage and installments."""

        tag = self._ensure_tag(user_id, payload.tag)
        transaction_model = payload.to_model(user_id)

        return self.add(
            transaction_model,
            tag=tag,
            installments_data=payload.installments,
        )

    def add(self, obj_in: Transaction, **kwargs: Any) -> TransactionResponse:
        """Persist a transaction entity and attach related records."""

        installments_data = kwargs.pop("installments_data", None)
        tag = kwargs.get("tag")

        if installments_data:
            obj_in.has_installments = True

        created_transaction = super().add(obj_in, **kwargs)

        if installments_data:
            self.installment_service.create_for_transaction(
                created_transaction, installments_data
            )
            self.db.refresh(created_transaction)

        if tag:
            self.repository.attach_tag(created_transaction, tag)

        return self._build_transaction_response(created_transaction)

    def update(self, id: UUID, obj_in: Any, **kwargs: Any) -> TransactionResponse:
        """Update a transaction and return its response representation."""

        updated_transaction = super().update(id, obj_in, **kwargs)
        return self._build_transaction_response(updated_transaction)

    def create_transfer_transaction(
        self, obj_in: TransferTransactionCreate, **kwargs: Any
    ) -> TransferResponse:
        """Validate transfer transaction before creation"""

        user_id = kwargs.get("user_id")

        if not user_id:
            logger.warning(f"Attempt to create transfer transaction without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        # Validate that the user owns the from and to accounts
        if not self._validate_account_ownership(user_id, obj_in.from_account_id):
            raise HTTPException(
                status_code=403, detail="From account not found or access denied"
            )
        if not self._validate_account_ownership(user_id, obj_in.to_account_id):
            raise HTTPException(
                status_code=403, detail="To account not found or access denied"
            )
        # Validate that the from and to account are different
        if obj_in.from_account_id == obj_in.to_account_id:
            raise HTTPException(
                status_code=400, detail="From and to account cannot be the same"
            )
        # Validate that the amount is greater than zero
        if obj_in.amount <= 0:
            raise HTTPException(
                status_code=400, detail="Transaction amount must be greater than zero"
            )
        # Validate that the date is not in the future
        transaction_date = (
            obj_in.date.date() if isinstance(obj_in.date, datetime) else obj_in.date
        )
        current_date = datetime.now(timezone.utc).date()
        if transaction_date > current_date:
            raise HTTPException(
                status_code=400, detail="Transaction date cannot be in the future"
            )

        # Generate unique transfer id
        transfer_id = uuid4()

        transfer_category = self.category_service.get_transfer_category(user_id)
        # Create from transaction
        from_transaction = obj_in.build_from_transaction(
            user_id, transfer_id, transfer_category.id
        )
        # Create to transaction
        to_transaction = obj_in.build_to_transaction(
            user_id, transfer_id, transfer_category.id
        )
        # Add transactions to database
        self.repository.add(from_transaction)
        self.repository.add(to_transaction)

        return TransferResponse(
            id=from_transaction.id,
            user_id=from_transaction.user_id,
            from_account_id=from_transaction.account_id,
            to_account_id=to_transaction.account_id,
            transfer_id=from_transaction.id,
            amount=from_transaction.amount,
            currency=from_transaction.currency,
            created_at=from_transaction.created_at,
            updated_at=from_transaction.updated_at,
        )

    def before_create(self, obj_in: Transaction, **kwargs: Any) -> bool:
        """Validate transaction before creation"""
        # Validate transaction type before other business rules
        valid_types = {t.value for t in TransactionType}
        if obj_in.type not in valid_types:
            raise HTTPException(status_code=400, detail="Invalid transaction type")

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

        tag = kwargs.get("tag")
        if tag and not self.tag_service.repository.validate_tag_ownership(
            obj_in.user_id, tag.id
        ):
            raise HTTPException(
                status_code=403, detail="Tag not found or access denied"
            )

        # Validate the transaction is not in the future
        transaction_date = (
            obj_in.date.date() if isinstance(obj_in.date, datetime) else obj_in.date
        )
        current_date = datetime.now(timezone.utc).date()
        if transaction_date > current_date:
            raise HTTPException(
                status_code=400, detail="Transaction date cannot be in the future"
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

        # Validate transaction type when being updated
        type_value = None
        if payload:
            type_value = payload.get("type")
        else:
            type_value = getattr(obj_in, "type", None)

        if isinstance(type_value, str):
            valid_types = {t.value for t in TransactionType}
            if type_value not in valid_types:
                raise HTTPException(status_code=400, detail="Invalid transaction type")

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

    def delete(self, id: UUID, **kwargs: Any) -> Transaction:
        existing_transaction = self.before_delete(id, **kwargs)

        if existing_transaction.has_installments:
            self.installment_service.delete_by_transaction_id(existing_transaction.id)

        self._remove_transaction_tags(existing_transaction.id)

        return super().delete(id, **kwargs)

    def _build_search_response(
        self, transactions: List[Transaction]
    ) -> SearchResponse[TransactionResponse]:
        responses = [
            self._build_transaction_response(transaction)
            for transaction in transactions
        ]
        return SearchResponse(total=len(responses), results=responses)

    def _build_transaction_response(
        self, transaction: Transaction
    ) -> TransactionResponse:
        """Compose a transaction response with related entity metadata."""

        account_name = self._resolve_account_name(transaction)
        category_summary = self._resolve_category_summary(transaction)
        group_name = self._resolve_group_name(transaction)
        installments = self._resolve_installments(transaction)
        tag_entity = self._resolve_tag(transaction)

        account_entity = TransactionRelatedEntity(
            id=transaction.account_id,
            name=account_name,
        )
        category_entity = category_summary
        group_entity = (
            TransactionRelatedEntity(id=transaction.group_id, name=group_name)
            if transaction.group_id
            else None
        )

        return TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            account=account_entity,
            category=category_entity,
            group=group_entity,
            tag=tag_entity,
            recurrent_transaction_id=transaction.recurrent_transaction_id,
            transfer_id=transaction.transfer_id,
            type=transaction.type,
            amount=transaction.amount,
            currency=transaction.currency,
            date=transaction.date,
            source=transaction.source,
            has_installments=transaction.has_installments,
            has_debt=transaction.has_debt,
            installments=installments,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
        )

    def _resolve_account_name(self, transaction: Transaction) -> str:
        account = getattr(transaction, "account", None)
        if account and getattr(account, "name", None):
            return account.name

        account_obj = self.account_service.get(transaction.account_id)
        return account_obj.name

    def _resolve_category_summary(
        self, transaction: Transaction
    ) -> CategoryResponseBase:
        category = getattr(transaction, "category", None)
        if category and getattr(category, "name", None):
            return CategoryResponseBase(
                id=transaction.category_id,
                name=category.name,
                icon=getattr(category, "icon", None),
                color=getattr(category, "color", None),
            )

        category_obj = self.category_service.get(transaction.category_id)
        return CategoryResponseBase(
            id=transaction.category_id,
            name=category_obj.name,
            icon=getattr(category_obj, "icon", None),
            color=getattr(category_obj, "color", None),
        )

    def _resolve_group_name(self, transaction: Transaction) -> Optional[str]:
        if transaction.group_id is None:
            return None

        group = getattr(transaction, "group", None)
        if group and getattr(group, "name", None):
            return group.name

        group_obj = (
            self.db.query(Group).filter(Group.id == transaction.group_id).first()
        )
        return group_obj.name if group_obj else None

    def _resolve_installments(
        self, transaction: Transaction
    ) -> Optional[List[InstallmentBase]]:
        if not transaction.has_installments:
            return None

        installments_rel = getattr(transaction, "installments", None)
        if installments_rel is not None:
            return [InstallmentBase.model_validate(i) for i in installments_rel]

        installments = self.installment_service.repository.get_by_transaction_id(
            transaction.id
        )
        return [InstallmentBase.model_validate(i) for i in installments]

    def _resolve_tag(
        self, transaction: Transaction
    ) -> Optional[TransactionRelatedEntity]:
        tags_rel = getattr(transaction, "transaction_tags", None)
        association = None

        if tags_rel:
            association = next(iter(tags_rel), None)
        if association is None:
            association = (
                self.db.query(TransactionTag)
                .filter(TransactionTag.transaction_id == transaction.id)
                .first()
            )

        if association is None:
            return None

        tag_obj = getattr(association, "tag", None)
        if tag_obj is None:
            tag_obj = self.db.query(Tag).filter(Tag.id == association.tag_id).first()

        if tag_obj is None:
            return TransactionRelatedEntity(id=association.tag_id, name=None)

        return TransactionRelatedEntity(id=tag_obj.id, name=tag_obj.name)

    def _ensure_tag(
        self,
        user_id: UUID,
        tag_payload: Optional[TagTransactionCreate],
    ) -> Optional[Tag]:
        """Return a tag id ensuring it exists and belongs to the user, creating it if needed."""

        if tag_payload is None:
            return None

        if tag_payload.id is None:
            created_tag = self.tag_service.add(tag_payload.to_model(user_id))
            return created_tag

        tag = self.tag_service.get(tag_payload.id)

        if tag is None:
            raise HTTPException(status_code=404, detail="Tag not found")
        if tag.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Tag not found or access denied"
            )
        return tag

    def _remove_transaction_tags(self, transaction_id: UUID) -> None:
        """Remove all tag associations for the provided transaction."""
        try:
            deleted = (
                self.db.query(TransactionTag)
                .filter(TransactionTag.transaction_id == transaction_id)
                .delete(synchronize_session=False)
            )
            if deleted:
                logger.info(
                    "Removed %s tag associations for transaction %s",
                    deleted,
                    transaction_id,
                )
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error(
                "Error removing tag associations for transaction %s: %s",
                transaction_id,
                exc,
            )
            raise HTTPException(
                status_code=500, detail="Error removing transaction tags"
            )

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
            return self.group_service.user_has_access(group_id, user_id)
        except Exception as exc:
            logger.warning(
                "Error validating group ownership for user %s and group %s: %s",
                user_id,
                group_id,
                exc,
            )
            return False
