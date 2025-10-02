import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import NUMERIC, UUID
from sqlalchemy.orm import relationship

from app.config.db_base import Base


class AccountType(str, Enum):
    CASH = "cash"
    CREDIT = "credit_card"
    DEBIT = "debit_card"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False, default=AccountType.CASH.value)
    currency = Column(Text, default="MXN")
    color = Column(Text, nullable=True)
    initial_balance = Column(NUMERIC, default=0)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    is_deleted = Column(Boolean, default=False)
    user = relationship("User", back_populates="accounts")
