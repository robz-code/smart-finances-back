from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.category_dependencies import get_category_service
from app.dependencies.user_dependencies import get_current_user
from app.entities.user import User
from app.schemas.base_schemas import SearchResponse
from app.schemas.category_schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.services.category_service import CategoryService

router = APIRouter()


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(get_current_user)],
)
def read_category(
    category_id: UUID, service: CategoryService = Depends(get_category_service)
) -> CategoryResponse:
    """
    Get a specific category by ID.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get(category_id)


@router.get("", response_model=SearchResponse[CategoryResponse])
def read_categories_list(
    service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
) -> SearchResponse[CategoryResponse]:
    """
    Get a list of all categories.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get_by_user_id(cast(UUID, current_user.id))


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """
    Create a new category.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.add(category_data.to_model(cast(UUID, current_user.id)))


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """
    Update a category if it belongs to the current user.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.update(
        category_id,
        category_data,
        user_id=cast(UUID, current_user.id),
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> None:
    """
    Delete a category if it belongs to the current user.

    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    service.delete(category_id, user_id=cast(UUID, current_user.id))
    return None
