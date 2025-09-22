import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.config.db_base import Base


class User(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    phone_number = Column(Text)
    is_registered = Column(Boolean, default=False)
    currency = Column(Text)
    language = Column(Text)
    profile_image = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationships
    tags = relationship("Tag", back_populates="user")
    accounts = relationship("Account", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    categories = relationship("Category", back_populates="user")
    user_debts_from = relationship(
        "UserDebt",
        foreign_keys="[UserDebt.from_user_id]",
        back_populates="from_user",
    )
    user_debts_to = relationship(
        "UserDebt",
        foreign_keys="[UserDebt.to_user_id]",
        back_populates="to_user",
    )
    recurring_debts_from = relationship(
        "RecurringDebt",
        foreign_keys="[RecurringDebt.from_user_id]",
        back_populates="from_user",
    )
    recurring_debts_to = relationship(
        "RecurringDebt",
        foreign_keys="[RecurringDebt.to_user_id]",
        back_populates="to_user",
    )

    # Bidirectional contacts relationship using many-to-many self-relationship
    contacts = relationship(
        "User",
        secondary="user_contacts",
        primaryjoin="User.id==user_contacts.c.user1_id",
        secondaryjoin="User.id==user_contacts.c.user2_id",
        backref="contacted_by",
    )

    group_memberships = relationship("GroupMember", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    recurring_transactions = relationship("RecurringTransaction", back_populates="user")
