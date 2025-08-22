import re
from datetime import UTC, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl, field_validator

from app.entities.user import User


class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    currency: Optional[Literal["USD", "EUR", "MXN"]] = None
    language: Optional[Literal["en", "es"]] = None
    profile_image: Optional[HttpUrl] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if v is None:
            return v

        # Only accept format: +[country_code][phone_number]
        # Examples: +1234567890, +521234567890
        phone_pattern = re.compile(r"^\+[1-9]\d{6,14}$")
        if not phone_pattern.match(v):
            raise ValueError(
                "Phone number must be in international format: +[country_code][phone_number] (e.g., +1234567890, +521234567890)"
            )

        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")
        if len(v.strip()) > 100:
            raise ValueError("Name cannot exceed 100 characters")
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-ZÀ-ÿ0-9\s\'-]+$", v.strip()):
            raise ValueError(
                "Name can only contain letters, spaces, hyphens, and apostrophes"
            )
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not v:
            raise ValueError("Email cannot be empty")
        # Additional email validation beyond Pydantic's EmailStr
        if len(v) > 254:  # RFC 5321 limit
            raise ValueError("Email address too long")
        return v.lower().strip()

    class Config:
        from_attributes = True


class UserProfile(UserBase):
    id: UUID
    is_registered: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(UserBase):

    class Config:
        from_attributes = True

    def to_model(self, current_user_id: UUID):
        return User(
            id=current_user_id,
            name=self.name,
            email=self.email,
            is_registered=True,
            phone_number=self.phone_number,
            currency=self.currency,
            language=self.language,
            profile_image=(
                str(self.profile_image) if self.profile_image is not None else None
            ),
            created_at=datetime.now(UTC),
        )

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number,
            "currency": self.currency,
            "language": self.language,
            "profile_image": self.profile_image,
            "created_at": datetime.now(UTC),
        }


class UserUpdate(UserBase):
    is_registered: Optional[bool] = None

    class Config:
        from_attributes = True

    def to_model(self, current_user_id: UUID):
        # Build a partial update model preserving None for unchanged fields
        updated = User(
            id=current_user_id,
            name=self.name,
            email=self.email,
            phone_number=self.phone_number,
            currency=self.currency,
            language=self.language,
            profile_image=(
                str(self.profile_image) if self.profile_image is not None else None
            ),
            is_registered=self.is_registered,
        )
        return updated

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number,
            "currency": self.currency,
            "language": self.language,
            "profile_image": self.profile_image,
            "is_registered": self.is_registered,
        }
