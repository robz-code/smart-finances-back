from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.entities.category import Category, CategoryType
from app.schemas.base_schemas import SearchResponse
from app.schemas.reporting_schemas import (
    CategoryAggregationData,
    CategorySummaryResponse,
    ReportingParameters,
    TransactionSummaryPeriod,
)
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
        parameters: ReportingParameters,
    ) -> SearchResponse[CategorySummaryResponse]:
        """
        Get categories with their transaction amounts for a given period or date range.

        Uses period (day/week/month/year) OR date_from/date_to. Period takes precedence.
        Applies all optional filters from parameters: account_id, category_id, category_type,
        transaction_type, currency, amount_min, amount_max, source.

        Args:
            user_id: User ID to filter categories and transactions
            parameters: Reporting parameters including date range and optional filters

        Returns:
            SearchResponse containing CategorySummaryResponse objects with transaction amounts
        """
        # 1. Resolve date range: period takes precedence over date_from/date_to
        if parameters.period is not None:
            date_from, date_to = calculate_period_dates(parameters.period)
        else:
            date_from = parameters.date_from
            date_to = parameters.date_to
            assert date_from is not None and date_to is not None  # validated by schema

        # 2. Fetch categories via CategoryService
        if parameters.category_type is not None:
            categories_response = self.category_service.get_by_user_id_and_type(
                user_id, parameters.category_type
            )
        else:
            categories_response = self.category_service.get_by_user_id(user_id)

        categories: List[Category] = categories_response.results

        # If category_id filter is set, restrict to that single category
        if parameters.category_id is not None:
            categories = [c for c in categories if c.id == parameters.category_id]
            if not categories:
                return SearchResponse(total=0, results=[])

        # 3. Get aggregated transaction amounts and counts via TransactionService (single query)
        category_ids = [cat.id for cat in categories]
        transaction_type_value = (
            parameters.transaction_type.value
            if parameters.transaction_type is not None
            else None
        )
        amounts_and_counts_by_category = (
            self.transaction_service.get_net_signed_amounts_and_counts_by_category(
                user_id=user_id,
                date_from=date_from,
                date_to=date_to,
                category_ids=category_ids if category_ids else None,
                account_id=parameters.account_id,
                transaction_type=transaction_type_value,
                currency=parameters.currency,
                amount_min=parameters.amount_min,
                amount_max=parameters.amount_max,
                source=parameters.source,
            )
        )

        # 4. Merge and return enriched response
        category_summaries = []
        for cat in categories:
            aggregation_data = amounts_and_counts_by_category.get(
                cat.id,
                CategoryAggregationData(
                    net_signed_amount=Decimal("0"), transaction_count=0
                ),
            )
            category_summaries.append(
                CategorySummaryResponse(
                    id=cat.id,
                    name=cat.name,
                    type=CategoryType(cat.type),
                    icon=cat.icon,
                    color=cat.color,
                    transaction_amount=aggregation_data.net_signed_amount,
                    transaction_count=aggregation_data.transaction_count,
                )
            )

        return SearchResponse(total=len(category_summaries), results=category_summaries)
