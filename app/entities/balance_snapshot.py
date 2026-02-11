"""
Balance snapshot entity.

CORE FINANCIAL PRINCIPLE (see docs/migrations/001_balance_snapshots.sql):
Snapshots are a performance optimization. They store balance at the start of a month
in the account's native currency, are deterministic and rebuildable, and are created
lazily. No converted balances are stored; FX is applied at read time only.
"""

import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import DATE, UUID

from app.config.db_base import Base


class BalanceSnapshot(Base):
    """
    Monthly balance cache per account.

    - snapshot_date is always the first day of the month (balance at start of that day).
    - balance = account.initial_balance + sum(transactions with date < snapshot_date).
    - Stored in account currency only; never store FX-converted balances.
    """

    __tablename__ = "balance_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    currency = Column(Text, nullable=False)
    snapshot_date = Column(DATE, nullable=False)
    balance = Column(Numeric, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc)
    )
