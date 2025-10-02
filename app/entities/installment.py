import uuid

from sqlalchemy import Column, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import NUMERIC, UUID
from sqlalchemy.orm import relationship

from app.config.db_base import Base


class Installment(Base):
    __tablename__ = "installments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    installment_number = Column(Integer)
    due_date = Column(Date)
    amount = Column(NUMERIC, nullable=False)
    transaction = relationship("Transaction", back_populates="installments")
