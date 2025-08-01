from app.repository.base_repository import BaseRepository
from sqlalchemy.orm import Session
from app.entities.user import User


class UserRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()
    