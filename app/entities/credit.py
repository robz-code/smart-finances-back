import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import DATE, NUMERIC, UUID

from app.config.database import Base


class Credit(Base):
    __tablename__ = "credits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), unique=True)
    type = Column(Text, nullable=False)
    limit = Column(NUMERIC)
    cutoff_day = Column(Integer)
    payment_due_day = Column(Integer)
    interest_rate = Column(NUMERIC)
    term_months = Column(Integer)
    start_date = Column(DATE)
    end_date = Column(DATE)
    grace_days = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    is_deleted = Column(Boolean, default=False)
