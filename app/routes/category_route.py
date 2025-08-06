from fastapi import APIRouter, Depends, status
from app.dependencies.category_dependencies import get_category_service
from app.schemas.category_schemas import CategoryResponse
from app.schemas.base_schemas import SearchResponse
from app.dependencies.user_dependencies import get_current_user
from uuid import UUID
from app.services.category_service import CategoryService


router = APIRouter()

@router.get("/{category_id}", response_model=CategoryResponse, dependencies=[Depends(get_current_user)])
def read_category(category_id: UUID, service: CategoryService = Depends(get_category_service)):
    """
    Get a specific category by ID.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get(category_id)

@router.get("", response_model=SearchResponse[CategoryResponse])
def read_categories_list(service: CategoryService = Depends(get_category_service), current_user: User = Depends(get_current_user)):
    """
    Get a list of all categories.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get_by_user_id(current_user.id)