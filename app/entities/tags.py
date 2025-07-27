from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.config.database import Base
import datetime
import uuid

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), nullable=False)
    name = Column(Text, nullable=False)
    color = Column(Text)  # Optional color for UI display
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="tags")
    transaction_tags = relationship("TransactionTag", back_populates="tag")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', user_id={self.user_id})>"
