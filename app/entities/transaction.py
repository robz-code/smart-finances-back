import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import DATE, NUMERIC, UUID
from sqlalchemy.orm import relationship

from app.config.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"))
    recurrent_transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("recurring_transactions.id")
    )
    transfer_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    type = Column(Text, nullable=False)
    amount = Column(NUMERIC, nullable=False)
    currency = Column(Text)
    date = Column(DATE, nullable=False)
    source = Column(Text, default="manual")
    has_installments = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationships
    transaction_tags = relationship("TransactionTag", back_populates="transaction")
    user = relationship("User", back_populates="transactions")
    user_debts = relationship("UserDebt", back_populates="transaction")
