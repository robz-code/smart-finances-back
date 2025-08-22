from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, UTC
from uuid import UUID
from app.entities.user_contact import UserContact
from app.entities.user_debt import UserDebt
import re
class ContactBase(BaseModel):
    name: str
    email: EmailStr

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        if len(v.strip()) > 100:
            raise ValueError('Name cannot exceed 100 characters')
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r'^[a-zA-ZÀ-ÿ0-9\s\'-]+$', v.strip()):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip()

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v:
            raise ValueError('Email cannot be empty')
        # Additional email validation beyond Pydantic's EmailStr
        if len(v) > 254:  # RFC 5321 limit
            raise ValueError('Email address too long')
        return v.lower().strip()

    class Config:
        from_attributes = True

class ContactCreate(BaseModel):
    email: EmailStr

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v:
            raise ValueError('Email cannot be empty')
        return v.lower().strip()

class ContactDetail(BaseModel):
    relationship_id: UUID
    name: str
    email: str
    is_registered: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserDebtSummary(BaseModel):
    id: UUID
    amount: float
    type: str
    note: Optional[str]
    date: datetime
    from_user_id: UUID
    to_user_id: UUID

    class Config:
        from_attributes = True

class ContactWithDebts(BaseModel):
    contact: ContactDetail
    debts: List[UserDebtSummary]

    class Config:
        from_attributes = True

class ContactList(BaseModel):
    relationship_id: UUID
    name: str
    email: str
    is_registered: bool
    created_at: datetime

    class Config:
        from_attributes = True