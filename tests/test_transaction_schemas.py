import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.entities.transaction import Transaction
from app.schemas.transaction_schemas import (
    RecentTransactionsParams,
    TransactionBase,
    TransactionCreate,
    TransactionResponse,
    TransactionSearch,
    TransactionUpdate,
)


class TestTransactionBase:
    """Test TransactionBase schema"""

    def _build_payload(self) -> dict[str, dict[str, str]]:
        return {
            "account": {
                "id": str(uuid.uuid4()),
                "name": "Checking Account",
            },
            "category": {
                "id": str(uuid.uuid4()),
                "name": "Groceries",
                "type": "expense",
                "icon": None,
                "color": None,
            },
        }

    def test_transaction_base_valid_data(self):
        """Test TransactionBase with valid data"""
        # Arrange
        data = {
            **self._build_payload(),
            "concept": {
                "id": str(uuid.uuid4()),
                "name": "Shared Concept",
            },
            "type": "expense",
            "amount": "100.50",
            "currency": "USD",
            "date": "2024-01-15",
            "source": "manual",
        }

        # Act
        transaction = TransactionBase(**data)

        # Assert - attributes
        assert str(transaction.account.id) == data["account"]["id"]
        assert transaction.account.name == data["account"]["name"]
        assert str(transaction.category.id) == data["category"]["id"]
        assert transaction.category.name == data["category"]["name"]
        assert transaction.concept is not None
        assert str(transaction.concept.id) == data["concept"]["id"]
        assert transaction.concept.name == data["concept"]["name"]
        assert transaction.type == "expense"
        assert transaction.amount == Decimal("100.50")
        assert transaction.currency == "USD"
        assert transaction.date == date(2024, 1, 15)
        assert transaction.source == "manual"

        # Assert - serialized output keeps nested structure
        serialized = transaction.model_dump(mode="json")
        assert serialized["account"] == data["account"]
        assert serialized["category"] == data["category"]
        assert serialized["concept"] == data["concept"]

    def test_transaction_base_minimal_data(self):
        """Test TransactionBase with minimal required data"""
        # Arrange
        data = {
            **self._build_payload(),
            "type": "income",
            "amount": "200.00",
            "date": "2024-01-20",
        }

        # Act
        transaction = TransactionBase(**data)

        # Assert
        assert str(transaction.account.id) == data["account"]["id"]
        assert transaction.account.name == data["account"]["name"]
        assert str(transaction.category.id) == data["category"]["id"]
        assert transaction.category.name == data["category"]["name"]
        assert transaction.concept is None
        assert transaction.type == "income"
        assert transaction.amount == Decimal("200.00")
        assert transaction.date == date(2024, 1, 20)
        assert transaction.source == "manual"  # default value
        assert transaction.currency is None

    def test_transaction_base_invalid_uuid(self):
        """Test TransactionBase with invalid UUID"""
        data = {
            **self._build_payload(),
            "type": "expense",
            "amount": "100.00",
            "date": "2024-01-15",
        }
        data["account"]["id"] = "invalid-uuid"

        with pytest.raises(ValidationError):
            TransactionBase(**data)

    def test_transaction_base_invalid_amount(self):
        """Test TransactionBase with invalid amount"""
        data = {
            **self._build_payload(),
            "type": "expense",
            "amount": "invalid-amount",
            "date": "2024-01-15",
        }

        with pytest.raises(ValidationError):
            TransactionBase(**data)

    def test_transaction_base_invalid_date(self):
        """Test TransactionBase with invalid date"""
        data = {
            **self._build_payload(),
            "type": "expense",
            "amount": "100.00",
            "date": "invalid-date",
        }

        with pytest.raises(ValidationError):
            TransactionBase(**data)


class TestTransactionCreate:
    """Test TransactionCreate schema"""

    def test_transaction_create_fields(self):
        """TransactionCreate exposes only creation-specific fields"""
        field_names = set(TransactionCreate.model_fields)
        assert field_names == {
            "account_id",
            "category_id",
            "concept",
            "tags",
            "type",
            "amount",
            "currency",
            "date",
            "source",
        }

    def test_transaction_create_to_model(self):
        """Test TransactionCreate to_model method"""
        # Arrange
        user_id = uuid.uuid4()
        data = {
            "account_id": str(uuid.uuid4()),
            "category_id": str(uuid.uuid4()),
            "type": "income",
            "amount": "500.00",
            "date": "2024-01-25",
        }
        transaction_create = TransactionCreate(**data)

        # Act
        model = transaction_create.to_model(user_id)

        # Assert
        assert isinstance(model, Transaction)
        assert model.user_id == user_id
        assert str(model.account_id) == data["account_id"]
        assert str(model.category_id) == data["category_id"]
        assert model.type == "income"
        assert model.amount == Decimal("500.00")
        assert model.date == date(2024, 1, 25)
        assert model.updated_at is None

    def test_transaction_create_with_new_concept(self):
        """TransactionCreate accepts new concept payloads"""
        data = {
            "account_id": str(uuid.uuid4()),
            "category_id": str(uuid.uuid4()),
            "type": "expense",
            "amount": "75.00",
            "date": "2024-01-10",
            "concept": {
                "name": "Dining",
                "color": "#FFAA00",
            },
        }

        transaction_create = TransactionCreate(**data)

        assert transaction_create.concept is not None
        assert transaction_create.concept.name == "Dining"


class TestTransactionUpdate:
    """Test TransactionUpdate schema"""

    def test_transaction_update_all_optional(self):
        """Test TransactionUpdate with all fields optional"""
        # Arrange
        data = {}

        # Act
        transaction_update = TransactionUpdate(**data)

        # Assert
        assert transaction_update.account_id is None
        assert transaction_update.category_id is None
        assert transaction_update.type is None
        assert transaction_update.amount is None
        assert transaction_update.currency is None
        assert transaction_update.date is None
        assert transaction_update.source is None

    def test_transaction_update_partial_data(self):
        """Test TransactionUpdate with partial data"""
        # Arrange
        data = {
            "amount": "150.00",
            "type": "expense",
        }

        # Act
        transaction_update = TransactionUpdate(**data)

        # Assert
        assert transaction_update.amount == Decimal("150.00")
        assert transaction_update.type == "expense"
        assert transaction_update.account_id is None
        assert transaction_update.category_id is None

    def test_transaction_update_with_uuid_fields(self):
        """Test TransactionUpdate with UUID fields"""
        # Arrange
        account_id = str(uuid.uuid4())
        category_id = str(uuid.uuid4())
        data = {
            "account_id": account_id,
            "category_id": category_id,
        }

        # Act
        transaction_update = TransactionUpdate(**data)

        # Assert
        assert str(transaction_update.account_id) == account_id
        assert str(transaction_update.category_id) == category_id


class TestTransactionResponse:
    """Test TransactionResponse schema"""

    def test_transaction_response_inheritance(self):
        """Test that TransactionResponse inherits from TransactionBase"""
        assert issubclass(TransactionResponse, TransactionBase)

    def test_transaction_response_with_all_fields(self):
        """Test TransactionResponse with all fields"""
        # Arrange
        transaction_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        account_id = str(uuid.uuid4())
        category_id = str(uuid.uuid4())
        concept_id = str(uuid.uuid4())
        account = {"id": account_id, "name": "Checking Account"}
        category = {
            "id": category_id,
            "name": "Groceries",
            "type": "expense",
            "icon": "groceries",
            "color": "#00FF00",
        }
        concept = {"id": concept_id, "name": "Essentials"}
        data = {
            "id": transaction_id,
            "user_id": user_id,
            "account": account,
            "category": category,
            "concept": concept,
            "type": "expense",
            "amount": "100.00",
            "currency": "USD",
            "date": "2024-01-15",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T11:00:00Z",
        }

        # Act
        transaction_response = TransactionResponse(**data)

        # Assert
        assert str(transaction_response.id) == transaction_id
        assert str(transaction_response.user_id) == user_id
        assert str(transaction_response.account.id) == account_id
        assert transaction_response.account.name == "Checking Account"
        assert str(transaction_response.category.id) == category_id
        assert transaction_response.category.name == "Groceries"
        assert transaction_response.category.icon == "groceries"
        assert transaction_response.category.color == "#00FF00"
        assert transaction_response.concept is not None
        assert str(transaction_response.concept.id) == concept_id
        assert transaction_response.concept.name == "Essentials"
        assert transaction_response.type == "expense"
        assert transaction_response.amount == Decimal("100.00")
        assert transaction_response.currency == "USD"
        assert transaction_response.date == date(2024, 1, 15)

        serialized = transaction_response.model_dump(mode="json")
        assert serialized["account"] == account
        assert serialized["category"] == category
        assert serialized["concept"] == concept


class TestTransactionSearch:
    """Test TransactionSearch schema"""

    def test_transaction_search_no_filters(self):
        """Test TransactionSearch with no filters"""
        # Act
        search = TransactionSearch()

        # Assert
        assert search.account_id is None
        assert search.category_id is None
        assert search.type is None
        assert search.currency is None
        assert search.date_from is None
        assert search.date_to is None
        assert search.period is None
        assert search.amount_min is None
        assert search.amount_max is None
        assert search.source is None

    def test_transaction_search_with_filters(self):
        """Test TransactionSearch with various filters"""
        # Arrange
        account_id = str(uuid.uuid4())
        category_id = str(uuid.uuid4())
        # Act
        search = TransactionSearch(
            account_id=account_id,
            category_id=category_id,
            type="expense",
            currency="USD",
            date_from="2024-01-01",
            date_to="2024-01-31",
            amount_min="100.00",
            amount_max="500.00",
            source="manual",
        )

        # Assert
        assert str(search.account_id) == account_id
        assert str(search.category_id) == category_id
        assert search.type == "expense"
        assert search.currency == "USD"
        assert search.date_from == date(2024, 1, 1)
        assert search.date_to == date(2024, 1, 31)
        assert search.period is None
        assert search.amount_min == Decimal("100.00")
        assert search.amount_max == Decimal("500.00")
        assert search.source == "manual"

    def test_transaction_search_with_period(self):
        """Test TransactionSearch with predefined period"""
        search = TransactionSearch(period="month")
        assert search.period is not None
        assert search.period.value == "month"

    def test_transaction_search_rejects_period_and_date_range(self):
        """Reject period combined with custom date range"""
        with pytest.raises(ValidationError) as exc:
            TransactionSearch(
                period="month", date_from="2024-01-01", date_to="2024-01-31"
            )
        assert "Use either 'period' or 'date_from'/'date_to'" in str(exc.value)

    def test_transaction_search_requires_both_date_from_and_date_to(self):
        """Reject only one of date_from/date_to"""
        with pytest.raises(ValidationError) as exc:
            TransactionSearch(date_from="2024-01-01")
        assert "Both 'date_from' and 'date_to' must be provided together." in str(
            exc.value
        )

    def test_transaction_search_rejects_date_from_after_date_to(self):
        """Reject date_from > date_to"""
        with pytest.raises(ValidationError) as exc:
            TransactionSearch(date_from="2024-02-01", date_to="2024-01-01")
        assert "'date_from' must be before or equal to 'date_to'." in str(exc.value)

    def test_transaction_search_with_decimal_amounts(self):
        """Test TransactionSearch with decimal amount filters"""
        # Arrange
        amount_min = Decimal("50.00")
        amount_max = Decimal("200.00")

        # Act
        search = TransactionSearch(
            amount_min=amount_min,
            amount_max=amount_max,
        )

        # Assert
        assert search.amount_min == amount_min
        assert search.amount_max == amount_max

    def test_transaction_search_with_date_objects(self):
        """Test TransactionSearch with date objects"""
        # Arrange
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 31)

        # Act
        search = TransactionSearch(
            date_from=date_from,
            date_to=date_to,
        )

        # Assert
        assert search.date_from == date_from
        assert search.date_to == date_to

    def test_transaction_search_model_config(self):
        """Test TransactionSearch model configuration"""
        # Act
        search = TransactionSearch()

        # Assert
        assert hasattr(search, "model_config")
        assert search.model_config.get("from_attributes") is True
        assert "json_schema_extra" in search.model_config
        assert "example" in search.model_config["json_schema_extra"]


class TestSchemaValidation:
    """Test schema validation edge cases"""

    def test_transaction_base_missing_required_fields(self):
        """Test TransactionBase validation with missing required fields"""
        required_category = {"id": str(uuid.uuid4()), "name": "Groceries"}
        # Missing account
        with pytest.raises(ValidationError):
            TransactionBase(
                category=required_category,
                type="expense",
                amount="100.00",
                date="2024-01-15",
            )

        # Missing type
        with pytest.raises(ValidationError):
            TransactionBase(
                account={"id": str(uuid.uuid4()), "name": "Checking Account"},
                category=required_category,
                amount="100.00",
                date="2024-01-15",
            )

        # Missing amount
        with pytest.raises(ValidationError):
            TransactionBase(
                account={"id": str(uuid.uuid4()), "name": "Checking Account"},
                category=required_category,
                type="expense",
                date="2024-01-15",
            )

        # Missing date
        with pytest.raises(ValidationError):
            TransactionBase(
                account={"id": str(uuid.uuid4()), "name": "Checking Account"},
                category=required_category,
                type="expense",
                amount="100.00",
            )

    def test_transaction_base_invalid_field_types(self):
        """Test TransactionBase validation with invalid field types"""
        # Invalid amount (string instead of decimal)
        with pytest.raises(ValidationError):
            TransactionBase(
                account={"id": str(uuid.uuid4()), "name": "Checking Account"},
                category={"id": str(uuid.uuid4()), "name": "Groceries"},
                type="expense",
                amount="not-a-number",
                date="2024-01-15",
            )

        # Invalid date (string instead of date)
        with pytest.raises(ValidationError):
            TransactionBase(
                account={"id": str(uuid.uuid4()), "name": "Checking Account"},
                category={"id": str(uuid.uuid4()), "name": "Groceries"},
                type="expense",
                amount="100.00",
                date="not-a-date",
            )

    def test_transaction_search_invalid_filters(self):
        """Test TransactionSearch validation with invalid filters"""
        # Invalid UUID
        with pytest.raises(ValidationError):
            TransactionSearch(account_id="invalid-uuid")

        # Invalid amount
        with pytest.raises(ValidationError):
            TransactionSearch(amount_min="not-a-number")

        # Invalid date
        with pytest.raises(ValidationError):
            TransactionSearch(date_from="not-a-date")


class TestRecentTransactionsParams:
    def test_recent_transactions_params_requires_limit(self):
        with pytest.raises(ValidationError) as exc:
            RecentTransactionsParams()
        assert "limit is required." in str(exc.value)

    def test_recent_transactions_params_limit_enum(self):
        with pytest.raises(ValidationError) as exc:
            RecentTransactionsParams(limit=7)
        assert "limit must be one of: 5, 10, 20, 50, 100." in str(exc.value)

    def test_recent_transactions_params_rejects_date_filters(self):
        with pytest.raises(ValidationError) as exc:
            RecentTransactionsParams(limit=10, date_from="2024-01-01")
        assert "Recent transactions does not support date filters or period." in str(
            exc.value
        )

    def test_recent_transactions_params_accepts_valid_limit(self):
        params = RecentTransactionsParams(limit=20)
        assert params.limit == 20
