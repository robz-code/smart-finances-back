from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.config.database import Base


class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), primary_key=True)
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("categories.id"), primary_key=True
    )
