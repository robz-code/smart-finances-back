from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.entities.category import Category, CategoryType
from app.schemas.base_schemas import SearchResponse
from app.schemas.reporting_schemas import CategorySummaryResponse, TransactionSummaryPeriod
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.shared.helpers.date_helper import calculate_period_dates


class ReportingService:
    """
    Service for cross-domain reporting and aggregation.
    
    This service orchestrates data from multiple domain services to provide
    aggregated reports without creating circular dependencies.
    """

    def __init__(
        self,
        category_service: CategoryService,
        transaction_service: TransactionService,
    ):
        self.category_service = category_service
        self.transaction_service = transaction_service

    def get_categories_summary(
        self,
        user_id: UUID,
        period: TransactionSummaryPeriod,
        category_type: Optional[CategoryType] = None,
    ) -> SearchResponse[CategorySummaryResponse]:
        """
        Get categories with their transaction amounts for a given period.
        
        Args:
            user_id: User ID to filter categories and transactions
            period: Time period for transaction aggregation (day, week, month, year)
            category_type: Optional filter by category type (income/expense)
        
        Returns:
            SearchResponse containing CategorySummaryResponse objects with transaction amounts
        """
        # 1. Calculate date range from period
        date_from, date_to = calculate_period_dates(period)

        # 2. Fetch categories via CategoryService
        if category_type is not None:
            categories_response = self.category_service.get_by_user_id_and_type(
                user_id, category_type
            )
        else:
            categories_response = self.category_service.get_by_user_id(user_id)

        categories: List[Category] = categories_response.results

        # 3. Get aggregated transaction amounts via TransactionService
        category_ids = [cat.id for cat in categories]
        amounts_by_category = self.transaction_service.get_net_signed_amounts_by_category(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            category_ids=category_ids if category_ids else None,
        )

        # 4. Merge and return enriched response
        category_summaries = [
            CategorySummaryResponse(
                id=cat.id,
                name=cat.name,
                type=CategoryType(cat.type),
                icon=cat.icon,
                color=cat.color,
                transaction_amount=format(
                    amounts_by_category.get(cat.id, Decimal("0")), ".2f"
                ),
            )
            for cat in categories
        ]

        return SearchResponse(total=len(category_summaries), results=category_summaries)
