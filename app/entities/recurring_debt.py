from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from app.config.database import Base
import datetime
import uuid

class RecurringDebt(Base):
    __tablename__ = 'recurring_debt'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recurring_transaction_id = Column(UUID(as_uuid=True), ForeignKey('recurring_transactions.id'))
    from_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    to_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    amount = Column(NUMERIC, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow) 