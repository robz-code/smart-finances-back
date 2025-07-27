from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.repository.tag_repository import TagRepository
from app.schemas.tag_schemas import TagCreate, TagUpdate, TagResponse
from app.entities.tags import Tag

class TagService:
    def __init__(self):
        self.tag_repository = TagRepository()

    def get_user_tags(self, db: Session, user_id: UUID) -> List[TagResponse]:
        """Get all tags for a user"""
        tags = self.tag_repository.get_user_tags(db, user_id)
        return [TagResponse.from_orm(tag) for tag in tags]

    def create_tag(self, db: Session, user_id: UUID, tag_data: TagCreate) -> TagResponse:
        """Create a new tag for a user"""
        # Check if tag with same name already exists for this user
        existing_tag = self.tag_repository.get_tag_by_name_and_user(db, tag_data.name, user_id)
        if existing_tag:
            raise ValueError(f"Tag '{tag_data.name}' already exists for this user")
        
        tag = self.tag_repository.create_user_tag(
            db, user_id, tag_data.name, tag_data.color
        )
        return TagResponse.from_orm(tag)

    def update_tag(self, db: Session, tag_id: UUID, user_id: UUID, tag_data: TagUpdate) -> Optional[TagResponse]:
        """Update a tag if it belongs to the user"""
        tag = self.tag_repository.get_by_id(db, tag_id)
        if not tag or tag.user_id != user_id:
            return None
        
        if tag_data.name is not None:
            # Check if new name conflicts with existing tag
            existing_tag = self.tag_repository.get_tag_by_name_and_user(db, tag_data.name, user_id)
            if existing_tag and existing_tag.id != tag_id:
                raise ValueError(f"Tag '{tag_data.name}' already exists for this user")
            tag.name = tag_data.name
        
        if tag_data.color is not None:
            tag.color = tag_data.color
        
        db.commit()
        db.refresh(tag)
        return TagResponse.from_orm(tag)

    def delete_tag(self, db: Session, tag_id: UUID, user_id: UUID) -> bool:
        """Delete a tag if it belongs to the user"""
        return self.tag_repository.delete_user_tag(db, tag_id, user_id)

    def add_tags_to_transaction(self, db: Session, transaction_id: UUID, tag_ids: List[UUID], user_id: UUID) -> bool:
        """Add tags to a transaction, ensuring they belong to the user"""
        # Verify all tags belong to the user
        for tag_id in tag_ids:
            tag = self.tag_repository.get_by_id(db, tag_id)
            if not tag or tag.user_id != user_id:
                raise ValueError(f"Tag {tag_id} does not belong to user {user_id}")
        
        # Remove existing tags and add new ones
        self.tag_repository.remove_tags_from_transaction(db, transaction_id)
        if tag_ids:
            self.tag_repository.add_tags_to_transaction(db, transaction_id, tag_ids)
        return True 