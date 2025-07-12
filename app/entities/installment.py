from sqlalchemy import Column, Integer, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from app.config.database import Base
import uuid

class Installment(Base):
    __tablename__ = 'installments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.id'))
    installment_number = Column(Integer)
    due_date = Column(Date)
    amount = Column(NUMERIC, nullable=False) 