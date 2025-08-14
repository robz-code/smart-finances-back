from sqlalchemy import Column, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from app.config.database import Base
import datetime
import uuid
from sqlalchemy.orm import relationship

class UserDebt(Base):
    __tablename__ = 'user_debts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.id'), nullable=True)
    from_user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'))
    to_user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'))
    amount = Column(NUMERIC, nullable=False)
    type = Column(Text, nullable=False)
    note = Column(Text)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="user_debts_from")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="user_debts_to")
    transaction = relationship("Transaction", back_populates="user_debts") 