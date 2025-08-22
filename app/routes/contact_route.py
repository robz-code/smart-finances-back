from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.contact_dependencies import get_contact_service
from app.dependencies.user_dependencies import get_current_user
from app.entities.user import User
from app.schemas.contact_schemas import (
    ContactCreate,
    ContactDetail,
    ContactList,
    ContactWithDebts,
)
from app.services.contact_service import ContactService

router = APIRouter()


@router.post(
    "",
    response_model=ContactDetail,
    summary="Create a new contact",
    description=(
        "Create a new contact for the current user. "
        "If the contact email is already registered, creates a relationship. "
        "If not, creates a new inactive user."
    ),
)
async def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Create a new contact for the current user.

    - If the contact email is already registered, creates a relationship between users
    - If the contact email is not registered, creates a new inactive user and relationship
    - Requires authentication via JWT token
    """
    return contact_service.create_contact(current_user.id, contact_data)


@router.get(
    "",
    response_model=List[ContactList],
    summary="Get user contacts",
    description="Retrieve all contacts for the current authenticated user.",
)
async def get_contacts(
    current_user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Get all contacts for the current user.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return contact_service.get_user_contacts(current_user.id)


@router.get(
    "/{relationship_id}",
    response_model=ContactWithDebts,
    summary="Get contact details",
    description=(
        "Retrieve detailed information about a specific contact "
        "including debt information between users."
    ),
)
async def get_contact_detail(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Get detailed information about a specific contact.

    Returns contact information along with debt details between the current user and the contact.
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return contact_service.get_contact_detail(relationship_id)


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Delete a specific contact.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return contact_service.delete(relationship_id, user_id=current_user.id)
