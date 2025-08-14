from app.repository.base_repository import BaseRepository
from sqlalchemy.orm import Session
from app.entities.user_contact import UserContact
from app.entities.user import User
from typing import Optional, List
from uuid import UUID

class ContactRepository(BaseRepository[UserContact]):
    def __init__(self, db: Session):
        super().__init__(db, UserContact)

    def get_by_user_id(self, user_id: UUID) -> List[UserContact]:
        """Get all contacts for a specific user"""
        return self.db.query(UserContact).filter(UserContact.user_id == user_id).all()

    def get_contact_detail(self, user_id: UUID, contact_id: UUID) -> Optional[UserContact]:
        """Get a specific contact relationship between two users"""
        return self.db.query(UserContact).filter(
            UserContact.user_id == user_id,
            UserContact.contact_id == contact_id
        ).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        return self.db.query(User).filter(User.email == email).first()

    def create_contact_relationship(self, user_id: UUID, contact_id: UUID) -> UserContact:
        """Create a contact relationship between two users"""
        contact = UserContact(
            user_id=user_id,
            contact_id=contact_id
        )
        return self.add(contact)

    def get_user_debts(self, user_id: UUID, contact_id: UUID) -> List:
        """Get all debts between two users"""
        from app.entities.user_debt import UserDebt
        
        debts = self.db.query(UserDebt).filter(
            ((UserDebt.from_user_id == user_id) & (UserDebt.to_user_id == contact_id)) |
            ((UserDebt.from_user_id == contact_id) & (UserDebt.to_user_id == user_id))
        ).all()
        
        return debts