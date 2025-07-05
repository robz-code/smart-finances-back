from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from app.config.database import Base
import uuid

class Installment(Base):
    __tablename__ = 'installments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.id'))
    installment_number = Column(Integer)
    amount = Column(NUMERIC, nullable=False) 