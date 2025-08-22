import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import DATE, NUMERIC, UUID
from sqlalchemy.orm import relationship

from app.config.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    name = Column(Text, nullable=False)
    recurrence = Column(Text, nullable=False)
    start_date = Column(DATE)
    end_date = Column(DATE)
    amount = Column(NUMERIC, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    user = relationship("User", back_populates="budgets")
