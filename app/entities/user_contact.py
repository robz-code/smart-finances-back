import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID

from app.config.db_base import Base


class UserContact(Base):
    __tablename__ = "user_contacts"

    user1_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user2_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    __table_args__ = (CheckConstraint("user1_id < user2_id", name="check_user_order"),)
