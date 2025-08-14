from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.config.database import Base
import datetime
import uuid
from sqlalchemy.orm import relationship

class GroupMember(Base):
    __tablename__ = 'group_members'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey('groups.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'))
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="group_memberships") 