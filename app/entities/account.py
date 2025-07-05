from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from app.config.database import Base
import datetime
import uuid

class Account(Base):
    __tablename__ = 'accounts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False)
    currency = Column(Text)
    initial_balance = Column(NUMERIC, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False) 