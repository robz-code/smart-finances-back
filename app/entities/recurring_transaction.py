import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import DATE, NUMERIC, UUID
from sqlalchemy.orm import relationship

from app.config.db_base import Base


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"))
    type = Column(Text, nullable=False)
    amount = Column(NUMERIC, nullable=False)
    start_date = Column(DATE, nullable=False)
    rrule = Column(Text, nullable=False)
    note = Column(Text)
    source = Column(Text, default="manual")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
    user = relationship("User", back_populates="recurring_transactions")
