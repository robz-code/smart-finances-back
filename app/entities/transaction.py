import datetime
import uuid
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import DATE, NUMERIC, UUID
from sqlalchemy.orm import relationship

from app.config.db_base import Base


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionSource(str, Enum):
    MANUAL = "manual"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )
    transfer_id = Column(UUID(as_uuid=True))
    type = Column(Text, nullable=False)
    amount = Column(NUMERIC, nullable=False)
    currency = Column(Text)
    date = Column(DATE, nullable=False)
    source = Column(Text, default=TransactionSource.MANUAL.value)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationships
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    transaction_tags = relationship("TransactionTag", back_populates="transaction")
    user = relationship("User", back_populates="transactions")
