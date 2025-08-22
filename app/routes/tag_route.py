from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.tag_dependencies import get_tag_service
from app.dependencies.user_dependencies import get_current_user
from app.entities.user import User
from app.schemas.base_schemas import SearchResponse
from app.schemas.tag_schemas import TagCreate, TagResponse, TagUpdate
from app.services.tag_service import TagService

router = APIRouter()


@router.get("", response_model=SearchResponse[TagResponse])
def get_user_tags(
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
):
    """Get all tags for the current user"""
    return tag_service.get_by_user_id(current_user.id)


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
    dependencies=[Depends(get_current_user)],
)
def get_tag(tag_id: UUID, tag_service: TagService = Depends(get_tag_service)):
    """Get a tag by ID"""
    return tag_service.get(tag_id)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
):
    """Create a new tag for the current user"""
    return tag_service.add(tag_data.to_model(current_user.id))


@router.put("/{tag_id}", response_model=TagResponse, status_code=status.HTTP_200_OK)
def update_tag(
    tag_id: UUID,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
):
    """Update a tag if it belongs to the current user"""
    return tag_service.update(tag_id, tag_data, user_id=current_user.id)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: UUID,
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
):
    """Delete a tag if it belongs to the current user"""
    return tag_service.delete(tag_id, user_id=current_user.id)
