from app.services.base_service import BaseService
from app.repository.category_repository import CategoryRepository
from app.entities.category import Category
from typing import Optional
from uuid import UUID
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class CategoryService(BaseService[Category]):
    def __init__(self, db):
        repository = CategoryRepository(db)
        super().__init__(db, repository, Category)