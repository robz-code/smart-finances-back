from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.concept_dependencies import get_concept_service
from app.dependencies.user_dependencies import get_current_user
from app.entities.user import User
from app.schemas.base_schemas import SearchResponse
from app.schemas.concept_schemas import ConceptCreate, ConceptResponse, ConceptUpdate
from app.services.concept_service import ConceptService

router = APIRouter()


@router.get("", response_model=SearchResponse[ConceptResponse])
def get_user_concepts(
    current_user: User = Depends(get_current_user),
    concept_service: ConceptService = Depends(get_concept_service),
) -> SearchResponse[ConceptResponse]:
    """Get all concepts for the current user"""
    return concept_service.get_by_user_id(cast(UUID, current_user.id))


@router.get(
    "/{concept_id}",
    response_model=ConceptResponse,
    dependencies=[Depends(get_current_user)],
)
def get_concept(
    concept_id: UUID, concept_service: ConceptService = Depends(get_concept_service)
) -> ConceptResponse:
    """Get a concept by ID"""
    return concept_service.get(concept_id)


@router.post("", response_model=ConceptResponse, status_code=status.HTTP_201_CREATED)
def create_concept(
    concept_data: ConceptCreate,
    current_user: User = Depends(get_current_user),
    concept_service: ConceptService = Depends(get_concept_service),
) -> ConceptResponse:
    """Create a new concept for the current user"""
    return concept_service.add(concept_data.to_model(cast(UUID, current_user.id)))


@router.put(
    "/{concept_id}", response_model=ConceptResponse, status_code=status.HTTP_200_OK
)
def update_concept(
    concept_id: UUID,
    concept_data: ConceptUpdate,
    current_user: User = Depends(get_current_user),
    concept_service: ConceptService = Depends(get_concept_service),
) -> ConceptResponse:
    """Update a concept if it belongs to the current user"""
    return concept_service.update(
        concept_id, concept_data, user_id=cast(UUID, current_user.id)
    )


@router.delete("/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concept(
    concept_id: UUID,
    current_user: User = Depends(get_current_user),
    concept_service: ConceptService = Depends(get_concept_service),
) -> None:
    """Delete a concept if it belongs to the current user"""
    concept_service.delete(concept_id, user_id=cast(UUID, current_user.id))
    return None
