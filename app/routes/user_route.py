from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.dependencies.user_dependencies import get_user_service, get_current_user
from app.schemas.user_schemas import UserCreate, UserBase, UserUpdate
from app.entities.user import User
from app.dependencies.auth_dependency import verify_token

router = APIRouter()

@router.get("", 
            summary="Get all users",
            description="Retrieve a list of all users. Requires a valid JWT token in the Authorization header.")
async def read_users_list(service: UserService = Depends(get_user_service)):
    """
    Get a list of all users.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get_all()

@router.post("", response_model=UserBase,
             summary="Create a new user",
             description="Create a new user with the provided data. Requires a valid JWT token in the Authorization header.")
async def create_user(user_data: UserCreate, service: UserService = Depends(get_user_service), token_payload: dict = Depends(verify_token)):
    """
    Create a new user.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    
    return service.add(user_data.to_model(token_payload.get("sub")))

@router.get("/me", response_model=UserBase, 
           summary="Get current user profile",
           description="Retrieve the profile of the currently authenticated user. Requires a valid JWT token in the Authorization header.")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the current user's profile information.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return current_user

@router.put("/me", response_model=UserBase,

           summary="Update current user profile",
           description="Update the profile of the currently authenticated user. Requires a valid JWT token in the Authorization header.")
async def update_curent_user(user_data: UserUpdate, current_user: User = Depends(get_current_user), user_service: UserService = Depends(get_user_service)):
    """
    Update the current user's profile information.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return user_service.update(current_user.id, user_data.to_model(current_user.id))