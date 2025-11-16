import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.account import Account
from app.entities.category import Category
from app.entities.transaction import Transaction
from app.schemas.transaction_schemas import TransactionSearch, TransactionUpdate
from app.services.account_service import AccountService
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService


class TestTransactionService:
    """Test transaction service business logic"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_repository(self):
        """Mock transaction repository"""
        return Mock()

    @pytest.fixture
    def service(self, mock_db, mock_repository):
        """Transaction service instance"""
        svc = TransactionService(mock_db)
        svc.repository = mock_repository
        svc.account_service = Mock(spec=AccountService)
        svc.category_service = Mock(spec=CategoryService)
        account = Mock()
        account.name = "Primary Account"
        svc.account_service.get.return_value = account
        category = Mock()
        category.name = "General Category"
        svc.category_service.get.return_value = category
        mock_db.query.return_value.filter.return_value.first.return_value = None
        return svc

    @pytest.fixture
    def sample_transaction(self):
        """Sample transaction entity for testing"""
        return Transaction(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            type="expense",
            amount=Decimal("100.00"),
            currency="USD",
            date=date(2024, 1, 15),
            source="manual",
        )

    def _create_transaction(
        self, user_id: uuid.UUID, amount: str = "100.00"
    ) -> Transaction:
        transaction = Transaction(
            id=uuid.uuid4(),
            user_id=user_id,
            account_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            type="expense",
            amount=Decimal(amount),
            currency="USD",
            date=date(2024, 1, 15),
            source="manual",
        )
        account = Account(name="Primary Account")
        account.id = transaction.account_id
        transaction.account = account

        category = Category(name="General Category")
        category.id = transaction.category_id
        transaction.category = category

        return transaction

    def test_search_transactions_success(self, service, mock_repository):
        """Test successful transaction search"""
        # Arrange
        user_id = uuid.uuid4()
        search_params = TransactionSearch(type="expense")
        mock_transactions = [
            self._create_transaction(user_id, "100.00"),
            self._create_transaction(user_id, "200.00"),
        ]
        mock_repository.search.return_value = mock_transactions

        # Act
        result = service.search(user_id, search_params)

        # Assert
        assert result.total == 2
        assert all(r.account.name == "Primary Account" for r in result.results)
        assert all(r.category.name == "General Category" for r in result.results)
        mock_repository.search.assert_called_once_with(user_id, search_params)

    def test_search_transactions_error(self, service, mock_repository):
        """Test transaction search with error"""
        # Arrange
        user_id = uuid.uuid4()
        search_params = TransactionSearch(type="expense")
        mock_repository.search.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.search(user_id, search_params)

        assert exc_info.value.status_code == 500
        assert "Error searching transactions" in str(exc_info.value.detail)

    def test_get_by_account_id_success(self, service, mock_repository):
        """Test successful get by account ID"""
        # Arrange
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()
        mock_transactions = [
            self._create_transaction(user_id),
            self._create_transaction(user_id, "75.00"),
        ]
        mock_repository.get_by_account_id.return_value = mock_transactions

        # Act
        result = service.get_by_account_id(user_id, account_id)

        # Assert
        assert result.total == 2
        assert all(r.account.name == "Primary Account" for r in result.results)
        mock_repository.get_by_account_id.assert_called_once_with(user_id, account_id)

    def test_get_by_category_id_success(self, service, mock_repository):
        """Test successful get by category ID"""
        # Arrange
        user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        mock_transactions = [
            self._create_transaction(user_id),
            self._create_transaction(user_id, "60.00"),
        ]
        mock_repository.get_by_category_id.return_value = mock_transactions

        # Act
        result = service.get_by_category_id(user_id, category_id)

        # Assert
        assert result.total == 2
        assert all(r.category.name == "General Category" for r in result.results)
        mock_repository.get_by_category_id.assert_called_once_with(user_id, category_id)

    def test_get_by_date_range_success(self, service, mock_repository):
        """Test successful get by date range"""
        # Arrange
        user_id = uuid.uuid4()
        date_from = "2024-01-01"
        date_to = "2024-01-31"
        mock_transactions = [
            self._create_transaction(user_id, amount="120.00"),
            self._create_transaction(user_id, amount="80.00"),
        ]
        mock_repository.get_by_date_range.return_value = mock_transactions

        # Act
        result = service.get_by_date_range(user_id, date_from, date_to)

        # Assert
        assert result.total == 2
        assert all(r.account.name == "Primary Account" for r in result.results)
        mock_repository.get_by_date_range.assert_called_once_with(
            user_id, date_from, date_to
        )

    @patch(
        "app.services.transaction_service.TransactionService._validate_account_ownership"
    )
    @patch(
        "app.services.transaction_service.TransactionService._validate_category_ownership"
    )
    def test_before_create_success(
        self,
        mock_validate_category,
        mock_validate_account,
        service,
        sample_transaction,
    ):
        """Test successful before_create validation"""
        # Arrange
        mock_validate_account.return_value = True
        mock_validate_category.return_value = True

        # Act
        result = service.before_create(sample_transaction)

        # Assert
        assert result is True
        mock_validate_account.assert_called_once_with(
            sample_transaction.user_id, sample_transaction.account_id
        )
        mock_validate_category.assert_called_once_with(
            sample_transaction.user_id, sample_transaction.category_id
        )

    @patch(
        "app.services.transaction_service.TransactionService._validate_account_ownership"
    )
    def test_before_create_invalid_account(
        self, mock_validate_account, service, sample_transaction
    ):
        """Test before_create with invalid account"""
        # Arrange
        mock_validate_account.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.before_create(sample_transaction)

        assert exc_info.value.status_code == 403
        assert "Account not found or access denied" in str(exc_info.value.detail)

    @patch(
        "app.services.transaction_service.TransactionService._validate_account_ownership"
    )
    @patch(
        "app.services.transaction_service.TransactionService._validate_category_ownership"
    )
    def test_before_create_invalid_category(
        self, mock_validate_category, mock_validate_account, service, sample_transaction
    ):
        """Test before_create with invalid category"""
        # Arrange
        mock_validate_account.return_value = True
        mock_validate_category.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.before_create(sample_transaction)

        assert exc_info.value.status_code == 403
        assert "Category not found or access denied" in str(exc_info.value.detail)

    def test_before_create_zero_amount(self, service, sample_transaction):
        """Test before_create with zero amount"""
        # Arrange
        sample_transaction.amount = Decimal("0.00")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.before_create(sample_transaction)

        assert exc_info.value.status_code == 400
        assert "Transaction amount cannot be zero" in str(exc_info.value.detail)

    def test_before_create_missing_category(self, service, sample_transaction):
        """Test before_create without a category should fail"""
        # Arrange
        sample_transaction.category_id = None

        with patch.object(service, "_validate_account_ownership", return_value=True):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                service.before_create(sample_transaction)

        assert exc_info.value.status_code == 400
        assert "Category is required" in str(exc_info.value.detail)

    @patch(
        "app.services.transaction_service.TransactionService._validate_account_ownership"
    )
    @patch(
        "app.services.transaction_service.TransactionService._validate_category_ownership"
    )
    def test_before_update_success(
        self,
        mock_validate_category,
        mock_validate_account,
        service,
        sample_transaction,
    ):
        """Test successful before_update validation"""
        # Arrange
        transaction_id = uuid.uuid4()
        update_data = Mock()
        update_data.account_id = uuid.uuid4()
        update_data.category_id = uuid.uuid4()
        service.repository.get.return_value = sample_transaction
        mock_validate_account.return_value = True
        mock_validate_category.return_value = True

        # Act
        result = service.before_update(
            transaction_id, update_data, user_id=sample_transaction.user_id
        )

        # Assert
        assert result is True
        mock_validate_account.assert_called_once_with(
            sample_transaction.user_id, update_data.account_id
        )
        mock_validate_category.assert_called_once_with(
            sample_transaction.user_id, update_data.category_id
        )

    def test_before_update_transaction_not_found(self, service):
        """Test before_update with non-existent transaction"""
        # Arrange
        transaction_id = uuid.uuid4()
        update_data = Mock()
        service.repository.get.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.before_update(transaction_id, update_data)

        assert exc_info.value.status_code == 404
        assert "Transaction not found" in str(exc_info.value.detail)

    def test_before_update_missing_category(self, service, sample_transaction):
        """Test before_update rejects removing the category"""
        # Arrange
        transaction_id = uuid.uuid4()
        update_data = TransactionUpdate(category_id=None)
        service.repository.get.return_value = sample_transaction

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.before_update(
                transaction_id, update_data, user_id=sample_transaction.user_id
            )

        assert exc_info.value.status_code == 400
        assert "Category is required" in str(exc_info.value.detail)

    def test_before_update_unauthorized_user(self, service, sample_transaction):
        """Test before_update with unauthorized user"""
        # Arrange
        transaction_id = uuid.uuid4()
        update_data = Mock()
        service.repository.get.return_value = sample_transaction

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.before_update(transaction_id, update_data, user_id=uuid.uuid4())

        assert exc_info.value.status_code == 403
        assert "Access denied to this transaction" in str(exc_info.value.detail)

    def test_before_delete_success(self, service, sample_transaction):
        """Test successful before_delete validation"""
        # Arrange
        transaction_id = uuid.uuid4()
        service.repository.get.return_value = sample_transaction

        # Act
        result = service.before_delete(
            transaction_id, user_id=sample_transaction.user_id
        )

        # Assert
        assert result == sample_transaction

    def test_before_delete_transaction_not_found(self, service):
        """Test before_delete with non-existent transaction"""
        # Arrange
        transaction_id = uuid.uuid4()
        service.repository.get.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.before_delete(transaction_id)

        assert exc_info.value.status_code == 404
        assert "Transaction not found" in str(exc_info.value.detail)

    def test_before_delete_unauthorized_user(self, service, sample_transaction):
        """Test before_delete with unauthorized user"""
        # Arrange
        transaction_id = uuid.uuid4()
        service.repository.get.return_value = sample_transaction

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.before_delete(transaction_id, user_id=uuid.uuid4())

        assert exc_info.value.status_code == 403
        assert "Access denied to this transaction" in str(exc_info.value.detail)

    def test_validate_account_ownership_success(self, service):
        """Test successful account ownership validation"""
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()
        mock_account = Mock()
        mock_account.user_id = user_id
        service.account_service.get.return_value = mock_account

        result = service._validate_account_ownership(user_id, account_id)

        assert result is True
        service.account_service.get.assert_called_once_with(account_id)

    def test_validate_account_ownership_account_not_found(self, service):
        """Test account ownership validation with non-existent account"""
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()
        service.account_service.get.side_effect = HTTPException(
            status_code=404, detail="Account not found"
        )

        result = service._validate_account_ownership(user_id, account_id)

        assert result is False

    def test_validate_account_ownership_wrong_user(self, service):
        """Test account ownership validation with wrong user"""
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()
        mock_account = Mock()
        mock_account.user_id = uuid.uuid4()
        service.account_service.get.return_value = mock_account

        result = service._validate_account_ownership(user_id, account_id)

        assert result is False

    def test_validate_category_ownership_success(self, service):
        """Test successful category ownership validation"""
        user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        mock_category = Mock()
        mock_category.user_id = user_id
        service.category_service.get.return_value = mock_category

        result = service._validate_category_ownership(user_id, category_id)

        assert result is True
        service.category_service.get.assert_called_once_with(category_id)
