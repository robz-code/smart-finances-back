from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.config.database import Base
import datetime
import uuid

class Category(Base):
    __tablename__ = 'categories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    icon = Column(Text)
    color = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow) 