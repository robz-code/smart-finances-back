import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.installment import Installment
from app.entities.group import Group
from app.entities.group_member import GroupMember
from app.entities.transaction import Transaction, TransactionType
from app.repository.transaction_repository import TransactionRepository
from app.schemas.base_schemas import SearchResponse
from app.schemas.installment_schemas import InstallmentBase
from app.schemas.transaction_schemas import (
    TransactionResponse,
    TransactionSearch,
    TransferResponse,
    TransferTransactionCreate,
)
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

    def _build_search_response(
        self, transactions: List[Transaction]
    ) -> SearchResponse[TransactionResponse]:
        responses = self._build_transaction_responses(transactions)
        return SearchResponse(total=len(responses), results=responses)

    def _build_transaction_responses(
        self, transactions: List[Transaction]
    ) -> List[TransactionResponse]:
        account_cache: Dict[UUID, str] = {}
        category_cache: Dict[UUID, str] = {}
        group_cache: Dict[UUID, Optional[str]] = {}

        return [
            self._build_transaction_response(
                transaction, account_cache, category_cache, group_cache
            )
            for transaction in transactions
        ]

    def _build_transaction_response(
        self,
        transaction: Transaction,
        account_cache: Optional[Dict[UUID, str]] = None,
        category_cache: Optional[Dict[UUID, str]] = None,
        group_cache: Optional[Dict[UUID, Optional[str]]] = None,
    ) -> TransactionResponse:
        """Compose a transaction response with related entity metadata."""

        account_name = self._get_account_name(transaction.account_id, account_cache)
        category_name = self._get_category_name(
            transaction.category_id, category_cache
        )
        group_name = self._get_group_name(transaction.group_id, group_cache)
        installments = self._get_installments(transaction)

        return TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            account_id=transaction.account_id,
            account_name=account_name,
            category_id=transaction.category_id,
            category_name=category_name,
            group_id=transaction.group_id,
            group_name=group_name,
            recurrent_transaction_id=transaction.recurrent_transaction_id,
            transfer_id=transaction.transfer_id,
            type=transaction.type,
            amount=transaction.amount,
            currency=transaction.currency,
            date=transaction.date,
            source=transaction.source,
            has_installments=transaction.has_installments,
            installments=installments,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
        )

    def _get_account_name(
        self, account_id: UUID, cache: Optional[Dict[UUID, str]] = None
    ) -> str:
        if cache is not None and account_id in cache:
            return cache[account_id]

        account = self.account_service.get(account_id)
        if cache is not None:
            cache[account_id] = account.name
        return account.name

    def _get_category_name(
        self, category_id: UUID, cache: Optional[Dict[UUID, str]] = None
    ) -> str:
        if cache is not None and category_id in cache:
            return cache[category_id]

        category = self.category_service.get(category_id)
        if cache is not None:
            cache[category_id] = category.name
        return category.name

    def _get_group_name(
        self, group_id: Optional[UUID], cache: Optional[Dict[UUID, Optional[str]]] = None
    ) -> Optional[str]:
        if group_id is None:
            return None

        if cache is not None and group_id in cache:
            return cache[group_id]

        group = self.db.query(Group).filter(Group.id == group_id).first()
        group_name = group.name if group else None

        if cache is not None:
            cache[group_id] = group_name

        return group_name

    def _get_installments(
        self, transaction: Transaction
    ) -> Optional[List[InstallmentBase]]:
        if not transaction.has_installments:
            return None

        installments = (
            self.db.query(Installment)
            .filter(Installment.transaction_id == transaction.id)
            .order_by(Installment.installment_number.asc())
            .all()
        )

        if not installments:
            return None

        return [
            InstallmentBase.model_validate(installment) for installment in installments
        ]

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
