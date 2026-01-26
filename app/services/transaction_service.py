import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.category import CategoryType
from app.entities.concept import Concept
from app.entities.tag import Tag
from app.entities.transaction import Transaction, TransactionType
from app.repository.transaction_repository import TransactionRepository
from app.schemas.base_schemas import SearchResponse
from app.schemas.category_schemas import CategoryResponseBase
from app.schemas.concept_schemas import ConceptTransactionCreate
from app.schemas.reporting_schemas import CategoryAggregationData
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
from app.services.concept_service import ConceptService
from app.services.tag_service import TagService

logger = logging.getLogger(__name__)


class TransactionService(BaseService[Transaction]):
    def __init__(
        self,
        db: Session,
        account_service: AccountService,
        category_service: CategoryService,
        concept_service: ConceptService,
        tag_service: TagService,
    ):
        repository = TransactionRepository(db)
        super().__init__(db, repository, Transaction)
        self.account_service = account_service
        self.category_service = category_service
        self.concept_service = concept_service
        self.tag_service = tag_service

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

    def get_net_signed_amounts_and_counts_by_category(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date,
        category_ids: Optional[List[UUID]] = None,
    ) -> Dict[UUID, CategoryAggregationData]:
        """
        Get net-signed transaction amounts and counts grouped by category_id in a single query.

        This method provides both aggregation and count data for category summaries efficiently.
        Net-signed means: income transactions add to the total, expense transactions subtract.

        Args:
            user_id: User ID to filter transactions
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            category_ids: Optional list of category IDs to filter by. If None, includes all categories.

        Returns:
            Dictionary mapping category_id to CategoryAggregationData DTO
        """
        return self.repository.get_net_signed_amounts_and_counts_by_category(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            category_ids=category_ids,
        )

    def create_transaction(
        self, payload: TransactionCreate, *, user_id: UUID
    ) -> TransactionResponse:
        """Create a transaction from a payload, handling optional concept and tags linkage."""

        concept = self._ensure_concept(user_id, payload.concept)
        tags = self._ensure_tags(user_id, payload.tags)
        transaction_model = payload.to_model(user_id)

        # Set concept_id directly on the transaction
        if concept:
            transaction_model.concept_id = concept.id

        return self.add(transaction_model, tags=tags)

    def add(self, obj_in: Transaction, **kwargs: Any) -> TransactionResponse:
        """Persist a transaction entity and attach related records."""

        tags = kwargs.get("tags")
        created_transaction = super().add(obj_in, **kwargs)

        if tags:
            self.repository.attach_tags(created_transaction, tags)

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
        created_from_transaction = self.repository.add(from_transaction)
        created_to_transaction = self.repository.add(to_transaction)

        # Refresh transactions to ensure relationships are loaded
        self.db.refresh(created_from_transaction)
        self.db.refresh(created_to_transaction)

        # Build full transaction responses
        from_response = self._build_transaction_response(created_from_transaction)
        to_response = self._build_transaction_response(created_to_transaction)

        return TransferResponse(
            transfer_id=transfer_id,
            from_transaction=from_response,
            to_transaction=to_response,
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

        # Validate concept ownership if concept_id is provided
        if (
            obj_in.concept_id
            and not self.concept_service.repository.validate_concept_ownership(
                obj_in.user_id, obj_in.concept_id
            )
        ):
            raise HTTPException(
                status_code=403, detail="Concept not found or access denied"
            )

        # Validate tag ownership if tags are provided
        tags = kwargs.get("tags")
        if tags:
            for tag in tags:
                if not self.tag_service.repository.validate_tag_ownership(
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

        # Remove all tag associations before deleting transaction
        self.repository.remove_all_tags(existing_transaction.id)

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
        concept_entity = self._resolve_concept(transaction)
        tags_entities = self._resolve_tags(transaction)

        account_entity = TransactionRelatedEntity(
            id=transaction.account_id,
            name=account_name,
        )
        category_entity = category_summary

        return TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            account=account_entity,
            category=category_entity,
            concept=concept_entity,
            tags=tags_entities,
            transfer_id=transaction.transfer_id,
            type=transaction.type,
            amount=transaction.amount,
            currency=transaction.currency,
            date=transaction.date,
            source=transaction.source,
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
            category_type_value = (
                getattr(category, "type", None) or CategoryType.EXPENSE.value
            )
            return CategoryResponseBase(
                id=transaction.category_id,
                name=category.name,
                type=category_type_value,
                icon=getattr(category, "icon", None),
                color=getattr(category, "color", None),
            )

        category_obj = self.category_service.get(transaction.category_id)
        category_type_value = (
            getattr(category_obj, "type", None) or CategoryType.EXPENSE.value
        )
        return CategoryResponseBase(
            id=transaction.category_id,
            name=category_obj.name,
            type=category_type_value,
            icon=getattr(category_obj, "icon", None),
            color=getattr(category_obj, "color", None),
        )

    def _resolve_concept(
        self, transaction: Transaction
    ) -> Optional[TransactionRelatedEntity]:
        """Resolve the concept for a transaction."""
        if not transaction.concept_id:
            return None

        concept = getattr(transaction, "concept", None)
        if concept:
            return TransactionRelatedEntity(id=concept.id, name=concept.name)

        # If concept relationship not loaded, fetch it
        concept_obj = self.concept_service.repository.get(transaction.concept_id)
        if concept_obj is None:
            return TransactionRelatedEntity(id=transaction.concept_id, name=None)

        return TransactionRelatedEntity(id=concept_obj.id, name=concept_obj.name)

    def _ensure_concept(
        self,
        user_id: UUID,
        concept_payload: Optional[ConceptTransactionCreate],
    ) -> Optional[Concept]:
        """Return a concept ensuring it exists and belongs to the user, creating it if needed."""

        if concept_payload is None:
            return None

        if concept_payload.id is None:
            created_concept = self.concept_service.add(
                concept_payload.to_model(user_id)
            )
            return created_concept

        concept = self.concept_service.get(concept_payload.id)

        if concept is None:
            raise HTTPException(status_code=404, detail="Concept not found")
        if concept.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Concept not found or access denied"
            )
        return concept

    def _ensure_tags(
        self,
        user_id: UUID,
        tags_payload: Optional[List[TagTransactionCreate]],
    ) -> List[Tag]:
        """Return a list of tags ensuring they exist and belong to the user, creating them if needed."""

        if tags_payload is None or len(tags_payload) == 0:
            return []

        tags: List[Tag] = []
        for tag_payload in tags_payload:
            if tag_payload.id is None:
                # Create new tag
                if tag_payload.name is None:
                    raise HTTPException(
                        status_code=400, detail="Tag name is required when creating a new tag"
                    )
                created_tag = self.tag_service.add(tag_payload.to_model(user_id))
                tags.append(created_tag)
            else:
                # Reference existing tag
                tag = self.tag_service.get(tag_payload.id)
                if tag is None:
                    raise HTTPException(status_code=404, detail="Tag not found")
                if tag.user_id != user_id:
                    raise HTTPException(
                        status_code=403, detail="Tag not found or access denied"
                    )
                tags.append(tag)

        return tags

    def _resolve_tags(
        self, transaction: Transaction
    ) -> List[TransactionRelatedEntity]:
        """Resolve the tags for a transaction."""
        tags_rel = getattr(transaction, "transaction_tags", None)
        tags: List[TransactionRelatedEntity] = []

        if tags_rel:
            for transaction_tag in tags_rel:
                tag = getattr(transaction_tag, "tag", None)
                if tag:
                    tags.append(TransactionRelatedEntity(id=tag.id, name=tag.name))
                else:
                    # If tag relationship not loaded, fetch it
                    tag_obj = self.tag_service.repository.get(transaction_tag.tag_id)
                    if tag_obj:
                        tags.append(
                            TransactionRelatedEntity(id=tag_obj.id, name=tag_obj.name)
                        )

        return tags

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
