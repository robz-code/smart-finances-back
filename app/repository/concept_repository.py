from uuid import UUID

from sqlalchemy.orm import Session

from app.entities.concept import Concept
from app.repository.base_repository import BaseRepository


class ConceptRepository(BaseRepository[Concept]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Concept)

    def validate_concept_ownership(self, user_id: UUID, concept_id: UUID) -> bool:
        """Validate that the user owns the concept."""
        concept = self.db.query(Concept).filter(Concept.id == concept_id).first()
        return bool(concept and concept.user_id == user_id)
