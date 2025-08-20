from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.dependencies.user_dependencies import get_user_service, get_current_user
from app.schemas.user_schemas import UserCreate, UserBase, UserUpdate, UserProfile
from app.entities.user import User
from app.dependencies.auth_dependency import verify_token
from app.schemas.base_schemas import MessageResponse

router = APIRouter()

@router.post("", response_model=UserProfile,
             summary="Create a new user",
             description="Create a new user with the provided data. Requires a valid JWT token in the Authorization header.")
async def create_user(user_data: UserCreate, service: UserService = Depends(get_user_service), token_payload: dict = Depends(verify_token)):
    """
    Create a new user.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    from uuid import UUID
    current_user_id = UUID(token_payload.get("sub"))
    return service.add(user_data.to_model(current_user_id))

@router.get("/", response_model=UserProfile, 
           summary="Get current user profile",
           description="Retrieve the profile of the currently authenticated user. Requires a valid JWT token in the Authorization header.")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the current user's profile information.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return current_user

@router.put("/", response_model=UserProfile,
           summary="Update current user profile",
           description="Update the profile of the currently authenticated user. Requires a valid JWT token in the Authorization header.")
async def update_curent_user(user_data: UserUpdate, current_user: User = Depends(get_current_user), user_service: UserService = Depends(get_user_service)):
    """
    Update the current user's profile information.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return user_service.update(current_user.id, user_data.to_model(current_user.id))

@router.delete("/",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete current user",
               description="Delete the currently authenticated user. Requires a valid JWT token in the Authorization header.")
async def soft_delete_current_user(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends (get_user_service)):
    """
    Soft Delete the current user.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    service.delete(current_user.id)
    return None
