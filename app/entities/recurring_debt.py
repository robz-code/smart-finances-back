import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import NUMERIC, UUID
from sqlalchemy.orm import relationship

from app.config.db_base import Base


class RecurringDebt(Base):
    __tablename__ = "recurring_debt"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recurring_transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("recurring_transactions.id")
    )
    from_user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    to_user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    amount = Column(NUMERIC, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
    from_user = relationship(
        "User",
        foreign_keys=[from_user_id],
        back_populates="recurring_debts_from",
    )
    to_user = relationship(
        "User", foreign_keys=[to_user_id], back_populates="recurring_debts_to"
    )
