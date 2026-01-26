import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.config.db_base import Base


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    name = Column(Text, nullable=False)
    color = Column(Text)  # Optional color for UI display
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationships
    user = relationship("User", back_populates="concepts")
    transactions = relationship("Transaction", back_populates="concept")

    def __repr__(self) -> str:
        return f"<Concept(id={self.id}, name='{self.name}', user_id={self.user_id})>"
