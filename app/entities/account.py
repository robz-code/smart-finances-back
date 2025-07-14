from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from app.config.database import Base
from datetime import datetime, UTC
import uuid
from enum import Enum

class AccountType(Enum):
    CASH = "cash"
    CREDIT = "credit_card"
    DEBIT = "debit_card"

class Account(Base):
    __tablename__ = 'accounts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'))
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False, default=AccountType.CASH.value)
    currency = Column(Text, default="MXN")
    initial_balance = Column(NUMERIC, default=0)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    is_deleted = Column(Boolean, default=False) 