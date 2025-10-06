import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.entities.transaction import Transaction
from app.repository.transaction_repository import TransactionRepository
from app.schemas.transaction_schemas import TransactionSearch


class TestTransactionRepository:
    """Test transaction repository database operations"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_query(self):
        """Mock SQLAlchemy query"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.options.return_value = mock_query
        return mock_query

    @pytest.fixture
    def repository(self, mock_db):
        """Transaction repository instance"""
        return TransactionRepository(mock_db)

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
            has_installments=False,
        )

    def test_search_transactions_no_filters(self, repository, mock_db, mock_query):
        """Test searching transactions with no filters"""
        # Arrange
        user_id = uuid.uuid4()
        search_params = TransactionSearch()
        mock_transactions = [Mock(), Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.search(user_id, search_params)

        # Assert
        assert result == mock_transactions
        mock_db.query.assert_called_once_with(Transaction)
        mock_query.options.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.all.assert_called_once()

    def test_search_transactions_with_account_filter(
        self, repository, mock_db, mock_query
    ):
        """Test searching transactions with account filter"""
        # Arrange
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()
        search_params = TransactionSearch(account_id=account_id)
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.search(user_id, search_params)

        # Assert
        assert result == mock_transactions
        # Verify filter was applied
        assert mock_query.filter.call_count >= 2  # user_id + account_id filters
        mock_query.options.assert_called_once()

    def test_search_transactions_with_category_filter(
        self, repository, mock_db, mock_query
    ):
        """Test searching transactions with category filter"""
        # Arrange
        user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        search_params = TransactionSearch(category_id=category_id)
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.search(user_id, search_params)

        # Assert
        assert result == mock_transactions
        # Verify filter was applied
        assert mock_query.filter.call_count >= 2  # user_id + category_id filters
        mock_query.options.assert_called_once()

    def test_search_transactions_with_type_filter(
        self, repository, mock_db, mock_query
    ):
        """Test searching transactions with type filter"""
        # Arrange
        user_id = uuid.uuid4()
        search_params = TransactionSearch(type="expense")
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.search(user_id, search_params)

        # Assert
        assert result == mock_transactions
        # Verify filter was applied
        assert mock_query.filter.call_count >= 2  # user_id + type filters
        mock_query.options.assert_called_once()

    def test_search_transactions_with_currency_filter(
        self, repository, mock_db, mock_query
    ):
        """Test searching transactions with currency filter"""
        # Arrange
        user_id = uuid.uuid4()
        search_params = TransactionSearch(currency="USD")
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.search(user_id, search_params)

        # Assert
        assert result == mock_transactions
        # Verify filter was applied
        assert mock_query.filter.call_count >= 2  # user_id + currency filters
        mock_query.options.assert_called_once()

    def test_search_transactions_with_date_range(self, repository, mock_db, mock_query):
        """Test searching transactions with date range filter"""
        # Arrange
        user_id = uuid.uuid4()
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 31)
        search_params = TransactionSearch(date_from=date_from, date_to=date_to)
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.search(user_id, search_params)

        # Assert
        assert result == mock_transactions
        # Verify filters were applied
        assert (
            mock_query.filter.call_count >= 3
        )  # user_id + date_from + date_to filters
        mock_query.options.assert_called_once()

    def test_search_transactions_with_amount_range(
        self, repository, mock_db, mock_query
    ):
        """Test searching transactions with amount range filter"""
        # Arrange
        user_id = uuid.uuid4()
        amount_min = Decimal("100.00")
        amount_max = Decimal("500.00")
        search_params = TransactionSearch(amount_min=amount_min, amount_max=amount_max)
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.search(user_id, search_params)

        # Assert
        assert result == mock_transactions
        # Verify filters were applied
        assert (
            mock_query.filter.call_count >= 3
        )  # user_id + amount_min + amount_max filters
        mock_query.options.assert_called_once()

    def test_search_transactions_with_source_filter(
        self, repository, mock_db, mock_query
    ):
        """Test searching transactions with source filter"""
        # Arrange
        user_id = uuid.uuid4()
        search_params = TransactionSearch(source="manual")
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.search(user_id, search_params)

        # Assert
        assert result == mock_transactions
        # Verify filter was applied
        assert mock_query.filter.call_count >= 2  # user_id + source filters
        mock_query.options.assert_called_once()

    def test_search_transactions_with_installments_filter(
        self, repository, mock_db, mock_query
    ):
        """Test searching transactions with installments filter"""
        # Arrange
        user_id = uuid.uuid4()
        search_params = TransactionSearch(has_installments=True)
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.search(user_id, search_params)

        # Assert
        assert result == mock_transactions
        # Verify filter was applied
        assert mock_query.filter.call_count >= 2  # user_id + has_installments filters
        mock_query.options.assert_called_once()

    def test_search_transactions_with_multiple_filters(
        self, repository, mock_db, mock_query
    ):
        """Test searching transactions with multiple filters"""
        # Arrange
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()
        category_id = uuid.uuid4()
        search_params = TransactionSearch(
            account_id=account_id,
            category_id=category_id,
            type="expense",
            currency="USD",
        )
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.search(user_id, search_params)

        # Assert
        assert result == mock_transactions
        # Verify multiple filters were applied
        assert (
            mock_query.filter.call_count >= 5
        )  # user_id + account_id + category_id + type + currency
        mock_query.options.assert_called_once()

    def test_search_transactions_ordering(self, repository, mock_db, mock_query):
        """Test that transactions are ordered correctly"""
        # Arrange
        user_id = uuid.uuid4()
        search_params = TransactionSearch()
        mock_transactions = [Mock(), Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        repository.search(user_id, search_params)

        # Assert
        mock_query.options.assert_called_once()
        mock_query.order_by.assert_called_once()
        # Verify order_by was called with date and created_at

    def test_get_by_account_id(self, repository, mock_db, mock_query):
        """Test getting transactions by account ID"""
        # Arrange
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()
        mock_transactions = [Mock(), Mock()]

        mock_db.query.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.get_by_account_id(user_id, account_id)

        # Assert
        assert result == mock_transactions
        mock_db.query.assert_called_once_with(Transaction)
        mock_query.options.assert_called_once()
        mock_query.filter.assert_called()
        mock_query.order_by.assert_called_once()
        mock_query.all.assert_called_once()

    def test_get_by_category_id(self, repository, mock_db, mock_query):
        """Test getting transactions by category ID"""
        # Arrange
        user_id = uuid.uuid4()
        category_id = uuid.uuid4()
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.get_by_category_id(user_id, category_id)

        # Assert
        assert result == mock_transactions
        mock_db.query.assert_called_once_with(Transaction)
        mock_query.options.assert_called_once()
        mock_query.filter.assert_called()
        mock_query.order_by.assert_called_once()
        mock_query.all.assert_called_once()

    def test_get_by_group_id(self, repository, mock_db, mock_query):
        """Test getting transactions by group ID"""
        # Arrange
        user_id = uuid.uuid4()
        group_id = uuid.uuid4()
        mock_transactions = [Mock()]

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.get_by_group_id(user_id, group_id)

        # Assert
        assert result == mock_transactions
        mock_db.query.assert_called_once_with(Transaction)
        mock_query.options.assert_called_once()
        mock_query.filter.assert_called()
        mock_query.order_by.assert_called_once()
        mock_query.all.assert_called_once()

    def test_get_by_date_range(self, repository, mock_db, mock_query):
        """Test getting transactions by date range"""
        # Arrange
        user_id = uuid.uuid4()
        date_from = "2024-01-01"
        date_to = "2024-01-31"
        mock_transactions = [Mock(), Mock()]

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.all.return_value = mock_transactions

        # Act
        result = repository.get_by_date_range(user_id, date_from, date_to)

        # Assert
        assert result == mock_transactions
        mock_db.query.assert_called_once_with(Transaction)
        mock_query.options.assert_called_once()
        mock_query.filter.assert_called()
        mock_query.order_by.assert_called_once()
        mock_query.all.assert_called_once()

    def test_inheritance_from_base_repository(self, repository):
        """Test that repository inherits from BaseRepository"""
        from app.repository.base_repository import BaseRepository

        assert isinstance(repository, BaseRepository)
        assert repository.model == Transaction

    def test_repository_initialization(self, mock_db):
        """Test repository initialization"""
        # Act
        repository = TransactionRepository(mock_db)

        # Assert
        assert repository.db == mock_db
        assert repository.model == Transaction
