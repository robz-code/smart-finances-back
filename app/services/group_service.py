import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.entities.group import Group
from app.repository.group_repository import GroupRepository
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class GroupService(BaseService[Group]):
    def __init__(self, db: Session) -> None:
        repository = GroupRepository(db)
        super().__init__(db, repository, Group)

    def get_for_user(self, group_id: UUID, user_id: UUID) -> Optional[Group]:
        """Return the group when the user owns or belongs to it."""
        group = self.repository.get(group_id)
        if group is None:
            return None

        if getattr(group, "created_by", None) == user_id:
            return group

        membership = self.repository.get_membership(group_id, user_id)
        return group if membership else None

    def user_has_access(self, group_id: UUID, user_id: UUID) -> bool:
        """Check whether the given user has access to the given group."""
        try:
            return self.get_for_user(group_id, user_id) is not None
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Error validating group %s access for user %s: %s",
                group_id,
                user_id,
                exc,
            )
            return False
