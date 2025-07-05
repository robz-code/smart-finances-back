from sqlalchemy import Column, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.config.database import Base
import datetime
import uuid

class Group(Base):
    __tablename__ = 'groups'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow) 