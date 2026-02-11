"""Dependencies for balance snapshot repository (used by reporting and transaction services)."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.repository.balance_snapshot_repository import BalanceSnapshotRepository


def get_balance_snapshot_repository(
    db: Session = Depends(get_db),
) -> BalanceSnapshotRepository:
    return BalanceSnapshotRepository(db)
