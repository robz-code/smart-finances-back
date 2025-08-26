import logging
import re
from datetime import datetime, timezone
from typing import List, cast
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entities.user import User
from app.entities.user_contact import UserContact
from app.repository.contact_repository import ContactRepository
from app.schemas.contact_schemas import (
    ContactCreate,
    ContactDetail,
    ContactList,
    ContactWithDebts,
    UserDebtSummary,
)
from app.services.base_service import BaseService
from app.services.debt_service import DebtService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class ContactService(BaseService[UserContact]):
    def __init__(
        self, db: Session, user_service: UserService, debt_service: DebtService
    ) -> None:
        repository = ContactRepository(db)
        super().__init__(db, repository, UserContact)
        self.user_service = user_service
        self.debt_service = debt_service

    def _derive_name_from_email(self, email: str) -> str:
        local_part = email.split("@")[0] if email and "@" in email else ""
        candidate = re.sub(r"[._\-]+", " ", local_part).strip()
        if not candidate:
            return "Contact"
        return candidate.title()

    def create_contact(
        self, user_id: UUID, contact_data: ContactCreate
    ) -> ContactDetail:
        """Create a new contact for a user"""
        try:
            # Check if the contact already exists as a user using UserService
            # for security
            existing_user = self.user_service.get_by_email(contact_data.email)

            if existing_user:
                # Contact exists, create relationship
                if existing_user.id == user_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot add yourself as a contact",
                    )

                # Check if relationship already exists using the new repository method
                existing_relationship = self.repository.check_contact_exists(
                    user_id, existing_user.id
                )
                
                if existing_relationship:
                    raise HTTPException(
                        status_code=409,
                        detail="Contact relationship already exists",
                    )

                # Create the relationship using the new repository method
                created_relationship = self.repository.create_contact_relationship(
                    user_id, existing_user.id
                )
                
                logger.info(
                    f"Created contact relationship between user {user_id} "
                    f"and existing user {existing_user.id}"
                )

                return ContactDetail(
                    relationship_id=cast(UUID, created_relationship.user1_id),  # Use user1_id as relationship_id
                    name=cast(str, existing_user.name),
                    email=cast(str, existing_user.email),
                    is_registered=cast(bool, existing_user.is_registered),
                    created_at=cast(datetime, existing_user.created_at),
                    updated_at=cast(datetime, existing_user.updated_at),
                )
            else:
                # Contact doesn't exist, create new inactive user
                derived_name = self._derive_name_from_email(contact_data.email)
                new_user = User(
                    name=derived_name,
                    email=contact_data.email,
                    is_registered=False,
                    created_at=datetime.now(timezone.utc),  # Fix deprecation warning
                    updated_at=None,  # New user, never been updated
                )

                # Add the new user using UserService
                created_user = self.user_service.add(new_user)

                # Create the relationship using the new repository method
                created_relationship = self.repository.create_contact_relationship(
                    user_id, created_user.id
                )
                
                logger.info(
                    f"Created new inactive user {created_user.id} "
                    f"and contact relationship with user {user_id}"
                )

                return ContactDetail(
                    relationship_id=cast(UUID, created_relationship.user1_id),  # Use user1_id as relationship_id
                    name=cast(str, created_user.name),
                    email=cast(str, created_user.email),
                    is_registered=cast(bool, created_user.is_registered),
                    created_at=cast(datetime, created_user.created_at),
                    updated_at=cast(
                        datetime,
                        created_user.updated_at or created_user.created_at,
                    ),
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating contact: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create contact")

    def get_user_contacts(self, user_id: UUID) -> List[ContactList]:
        """Get all contacts for a user using the new repository method"""
        try:
            # Use the new repository method to get contact relationships
            contact_relationships = self.repository.get_contacts_by_user_id(user_id)
            contacts = []

            for relationship in contact_relationships:
                # Determine which user is the contact (not the current user)
                contact_user_id = (
                    relationship.user2_id if relationship.user1_id == user_id 
                    else relationship.user1_id
                )
                
                contact_user = self.user_service.get(contact_user_id)
                contacts.append(
                    ContactList(
                        relationship_id=cast(UUID, relationship.user1_id),  # Use user1_id as relationship_id
                        name=cast(str, contact_user.name),
                        email=cast(str, contact_user.email),
                        is_registered=cast(bool, contact_user.is_registered),
                        created_at=cast(datetime, contact_user.created_at),
                    )
                )

            return contacts
        except Exception as e:
            logger.error(f"Error getting user contacts: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve contacts")

    def get_contact_detail(self, relationship_id: UUID) -> ContactWithDebts:
        """Get detailed information about a specific contact including debts"""
        try:
            # Since we no longer have a single relationship ID, we need to find the relationship
            # by searching through the user's contacts
            # For now, we'll use the relationship_id as a user_id to find the contact
            # This is a temporary solution - in a real implementation, you might want to
            # restructure the API to use user_id instead of relationship_id
            
            # Find the relationship by searching for the user in contact relationships
            # This is not ideal but maintains backward compatibility
            relationships = self.repository.get_contacts_by_user_id(relationship_id)
            
            if not relationships:
                raise HTTPException(status_code=404, detail="Contact not found")
            
            # For simplicity, use the first relationship found
            # In a real implementation, you might want to restructure this
            relationship = relationships[0]
            
            # Determine which user is the contact
            contact_user_id = (
                relationship.user2_id if relationship.user1_id == relationship_id 
                else relationship.user1_id
            )

            # Get the contact user details using UserService
            contact_user = self.user_service.get(contact_user_id)

            # Get debts between the users
            debts = self.debt_service.get_user_debts(
                relationship_id, contact_user_id
            )

            # Convert debts to summary format
            debt_summaries = []
            for debt in debts:
                debt_summaries.append(
                    UserDebtSummary(
                        id=cast(UUID, debt.id),
                        amount=float(debt.amount),
                        type=cast(str, debt.type),
                        note=cast("str | None", debt.note),
                        date=cast(datetime, debt.date),
                        from_user_id=cast(UUID, debt.from_user_id),
                        to_user_id=cast(UUID, debt.to_user_id),
                    )
                )

            # Create ContactDetail first
            contact_detail = ContactDetail(
                relationship_id=cast(UUID, relationship.user1_id),  # Use user1_id as relationship_id
                name=cast(str, contact_user.name),
                email=cast(str, contact_user.email),
                is_registered=cast(bool, contact_user.is_registered),
                created_at=cast(datetime, contact_user.created_at),
                updated_at=cast(datetime, contact_user.updated_at),
            )

            return ContactWithDebts(
                contact=contact_detail,
                debts=debt_summaries,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting contact detail: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve contact details"
            )

    def delete_contact(self, relationship_id: UUID, user_id: UUID) -> bool:
        """Delete a contact relationship"""
        try:
            # Since we no longer have a single relationship ID, we need to find the relationship
            # by searching through the user's contacts
            # For now, we'll use the relationship_id as a user_id to find the contact
            # This is a temporary solution - in a real implementation, you might want to
            # restructure the API to use user_id instead of relationship_id
            
            # Find the relationship by searching for the user in contact relationships
            relationships = self.repository.get_contacts_by_user_id(relationship_id)
            
            if not relationships:
                raise HTTPException(status_code=404, detail="Contact not found")
            
            # For simplicity, use the first relationship found
            # In a real implementation, you might want to restructure this
            relationship = relationships[0]
            
            # Delete the relationship using the new repository method
            success = self.repository.delete_contact_relationship(
                relationship.user1_id, relationship.user2_id
            )
            
            if success:
                logger.info(f"Successfully deleted contact relationship between users {relationship.user1_id} and {relationship.user2_id}")
                return True
            else:
                raise HTTPException(status_code=404, detail="Contact relationship not found")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting contact: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete contact")
