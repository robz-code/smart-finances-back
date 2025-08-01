from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.config.database import get_db
from app.dependencies.user_dependencies import get_current_user
from app.dependencies.tag_dependencies import get_tag_service
from app.schemas.tag_schemas import TagCreate, TagUpdate, TagResponse, TagListResponse
from app.services.tag_service import TagService
from app.entities.user import User

router = APIRouter()

@router.get("/", response_model=TagListResponse)
def get_user_tags(
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service)
):
    """Get all tags for the current user"""
    tags = tag_service.get_by_user_id(current_user.id)
    return TagListResponse(tags=tags, total=len(tags))

@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service)
):
    """Create a new tag for the current user"""
    try:
        tag = tag_service.create_tag(db, current_user.id, tag_data)
        return tag
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: UUID,
    tag_data: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service)
):
    """Update a tag if it belongs to the current user"""
    try:
        tag = tag_service.update_tag(db, tag_id, current_user.id, tag_data)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found or does not belong to user"
            )
        return tag
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service)
):
    """Delete a tag if it belongs to the current user"""
    success = tag_service.delete_tag(db, tag_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found or does not belong to user"
        )