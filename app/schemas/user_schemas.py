from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, UTC
from app.entities.user import User
from uuid import UUID

class UserBase(BaseModel):
    
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    is_registered: Optional[bool] = True
    currency: Optional[str] = None
    language: Optional[str] = None
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True

class UserCreate(UserBase):

    class Config:
        from_attributes = True

    def to_model(self, current_user_id: UUID):
        return User(
            id=current_user_id,
            name=self.name,
            email=self.email,
            phone_number=self.phone_number,
            is_registered=self.is_registered,
            currency=self.currency,
            language=self.language,
            profile_image=self.profile_image,
            created_at=datetime.now(UTC),
        )

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number,
            "is_registered": self.is_registered,
            "currency": self.currency,
            "language": self.language,
            "profile_image": self.profile_image,
            "created_at": datetime.now(UTC),
        }
