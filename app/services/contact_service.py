import logging
import re
from datetime import UTC, datetime
from typing import List
from uuid import UUID

from fastapi import HTTPException

from app.entities.user import User
from app.entities.user_contact import UserContact
from app.repository.contact_repository import ContactRepository
from app.schemas.contact_schemas import (
    ContactCreate,
    ContactDetail,
    ContactList,
    ContactWithDebts,
)
from app.services.base_service import BaseService
from app.services.debt_service import DebtService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class ContactService(BaseService[UserContact]):
    def __init__(self, db, user_service: UserService, debt_service: DebtService):
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
            # Check if the contact already exists as a user using UserService for security
            existing_user = self.user_service.get_by_email(contact_data.email)

            if existing_user:
                # Contact exists, create relationship
                if existing_user.id == user_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot add yourself as a contact",
                    )

                # Check if relationship already exists using BaseService get_by_user_id
                existing_relationships_response = super().get_by_user_id(user_id)
                existing_relationship = next(
                    (
                        rel
                        for rel in existing_relationships_response.results
                        if rel.contact_id == existing_user.id
                    ),
                    None,
                )
                if existing_relationship:
                    raise HTTPException(
                        status_code=409,
                        detail="Contact relationship already exists",
                    )

                # Create the relationship using BaseService add method
                contact_relationship = UserContact(
                    user_id=user_id, contact_id=existing_user.id
                )
                created_relationship = super().add(contact_relationship)
                logger.info(
                    f"Created contact relationship between user {user_id} and existing user {existing_user.id}"
                )

                return ContactDetail(
                    relationship_id=created_relationship.id,  # Use the UserContact ID
                    name=existing_user.name,
                    email=existing_user.email,
                    is_registered=existing_user.is_registered,
                    created_at=existing_user.created_at,
                    updated_at=existing_user.updated_at,
                )
            else:
                # Contact doesn't exist, create new inactive user
                derived_name = self._derive_name_from_email(contact_data.email)
                new_user = User(
                    name=derived_name,
                    email=contact_data.email,
                    is_registered=False,
                    created_at=datetime.now(UTC),  # Fix deprecation warning
                    updated_at=None,  # New user, never been updated
                )

                # Add the new user using UserService
                created_user = self.user_service.add(new_user)

                # Create the relationship using BaseService add method
                contact_relationship = UserContact(
                    user_id=user_id, contact_id=created_user.id
                )
                created_relationship = super().add(contact_relationship)
                logger.info(
                    f"Created new inactive user {created_user.id} and contact relationship with user {user_id}"
                )

                return ContactDetail(
                    relationship_id=created_relationship.id,  # Use the UserContact ID
                    name=created_user.name,
                    email=created_user.email,
                    is_registered=created_user.is_registered,
                    created_at=created_user.created_at,
                    updated_at=created_user.updated_at or created_user.created_at,
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating contact: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create contact")

    def get_user_contacts(self, user_id: UUID) -> List[ContactList]:
        """Get all contacts for a user using BaseService method"""
        try:
            # Use BaseService method to get contact relationships
            contact_relationships = super().get_by_user_id(user_id)
            contacts = []

            for relationship in contact_relationships.results:
                contact_user = self.user_service.get(relationship.contact_id)
                contacts.append(
                    ContactList(
                        relationship_id=relationship.id,
                        name=contact_user.name,
                        email=contact_user.email,
                        is_registered=contact_user.is_registered,
                        created_at=contact_user.created_at,
                    )
                )

            return contacts
        except Exception as e:
            logger.error(f"Error getting user contacts: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve contacts")

    def get_contact_detail(self, relationship_id: UUID) -> ContactWithDebts:
        """Get detailed information about a specific contact including debts"""
        try:
            # Verify the contact relationship exists using BaseService get_by_user_id
            relationship = super().get(relationship_id)

            if not relationship:
                raise HTTPException(status_code=404, detail="Contact not found")

            # Get the contact user details using UserService
            contact_user = self.user_service.get(relationship.contact_id)

            # Get debts between the users
            debts = self.debt_service.get_user_debts(
                relationship.user_id, relationship.contact_id
            )

            # Convert debts to summary format
            debt_summaries = []
            for debt in debts:
                debt_summaries.append(
                    {
                        "id": debt.id,
                        "amount": float(debt.amount),
                        "type": debt.type,
                        "note": debt.note,
                        "date": debt.date,
                        "from_user_id": debt.from_user_id,
                        "to_user_id": debt.to_user_id,
                    }
                )

            return ContactWithDebts(
                contact=ContactDetail(
                    relationship_id=relationship.id,
                    name=contact_user.name,
                    email=contact_user.email,
                    is_registered=contact_user.is_registered,
                    created_at=contact_user.created_at,
                    updated_at=contact_user.updated_at,
                ),
                debts=debt_summaries,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting contact detail: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve contact details"
            )

    def before_delete(self, id: UUID, **kwargs) -> UserContact:
        contact = super().before_delete(id, **kwargs)

        user_id = kwargs.get("user_id")
        if not user_id:
            logger.warning(f"Attempt to delete contact with ID: {id} without user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID provided")

        if contact.user_id != user_id:
            logger.warning(
                f"Attempt to delete contact with ID: {id} not owned by user with ID: {user_id}"
            )
            raise HTTPException(status_code=403, detail="You do not own this contact")

        # Check if the contact is still in the user's contacts
        existing_relationships_response = super().get_by_user_id(user_id)
        existing_relationship = next(
            (
                rel
                for rel in existing_relationships_response.results
                if rel.contact_id == contact.contact_id
            ),
            None,
        )
        if not existing_relationship:
            logger.warning(
                f"Attempt to delete contact with ID: {id} not found in user's contacts"
            )
            raise HTTPException(status_code=404, detail="Contact not found")

        return contact
