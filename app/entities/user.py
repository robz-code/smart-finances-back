import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.config.database import Base


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
    contacts = relationship(
        "UserContact",
        foreign_keys="[UserContact.user_id]",
        back_populates="user",
    )
    contacts_of = relationship(
        "UserContact",
        foreign_keys="[UserContact.contact_id]",
        back_populates="contact",
    )
    group_memberships = relationship("GroupMember", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    recurring_transactions = relationship("RecurringTransaction", back_populates="user")
