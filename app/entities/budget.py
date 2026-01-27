import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import NUMERIC, UUID
from sqlalchemy.orm import relationship

from app.config.db_base import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    name = Column(Text, nullable=False)
    recurrence = Column(Text, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    amount = Column(NUMERIC, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    user = relationship("User", back_populates="budgets")
    account = relationship("Account", back_populates="budgets")
