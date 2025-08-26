from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.entities.user_contact import UserContact
from app.repository.base_repository import BaseRepository


class ContactRepository(BaseRepository[UserContact]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, UserContact)

    def get_user_debts(self, user_id: UUID, contact_id: UUID) -> List:
        """Get all debts between two users"""
        from app.entities.user_debt import UserDebt

        debts = (
            self.db.query(UserDebt)
            .filter(
                (
                    (UserDebt.from_user_id == user_id)
                    & (UserDebt.to_user_id == contact_id)
                )
                | (
                    (UserDebt.from_user_id == contact_id)
                    & (UserDebt.to_user_id == user_id)
                )
            )
            .all()
        )

        return debts

    def get_contacts_by_user_id(self, user_id: UUID) -> List[UserContact]:
        """Get all contact relationships for a user
        (works with both user1_id and user2_id)"""
        return (
            self.db.query(UserContact)
            .filter(
                (UserContact.user1_id == user_id) | (UserContact.user2_id == user_id)
            )
            .all()
        )

    def check_contact_exists(
        self, user1_id: UUID, user2_id: UUID
    ) -> Optional[UserContact]:
        """Check if a contact relationship already exists between two users"""
        # Ensure user1_id < user2_id for consistency
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id

        return (
            self.db.query(UserContact)
            .filter(
                (UserContact.user1_id == user1_id) & (UserContact.user2_id == user2_id)
            )
            .first()
        )

    def create_contact_relationship(
        self, user1_id: UUID, user2_id: UUID
    ) -> UserContact:
        """Create a new contact relationship between two users"""
        # Ensure user1_id < user2_id for consistency
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id

        contact_relationship = UserContact(user1_id=user1_id, user2_id=user2_id)

        return self.add(contact_relationship)

    def delete_contact_relationship(self, user1_id: UUID, user2_id: UUID) -> bool:
        """Delete a contact relationship between two users"""
        # Ensure user1_id < user2_id for consistency
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id

        relationship = (
            self.db.query(UserContact)
            .filter(
                (UserContact.user1_id == user1_id) & (UserContact.user2_id == user2_id)
            )
            .first()
        )

        if relationship:
            self.db.delete(relationship)
            self.db.commit()
            return True

        return False
