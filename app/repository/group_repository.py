from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.entities.group import Group
from app.entities.group_member import GroupMember
from app.repository.base_repository import BaseRepository


class GroupRepository(BaseRepository[Group]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Group)

    def get_membership(self, group_id: UUID, user_id: UUID) -> Optional[GroupMember]:
        """Return the group membership when the user belongs to the group."""
        return (
            self.db.query(GroupMember)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
            )
            .first()
        )
