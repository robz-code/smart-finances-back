import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.config.database import Base


class TransactionTag(Base):
    __tablename__ = "transaction_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False
    )
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    transaction = relationship("Transaction", back_populates="transaction_tags")
    tag = relationship("Tag", back_populates="transaction_tags")

    def __repr__(self) -> str:
        return f"<TransactionTag(transaction_id={self.transaction_id}, tag_id={self.tag_id})>"
