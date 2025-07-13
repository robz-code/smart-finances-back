from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.dependencies.user_dependencies import get_user_service, get_current_user
from app.schemas.user_schemas import UserCreate, UserBase
from app.entities.user import User

router = APIRouter()

@router.get("")
async def read_users_list(service: UserService = Depends(get_user_service)):
    return service.get_all()

@router.post("", response_model=UserBase, )
async def create_user(user_data: UserCreate, service: UserService = Depends(get_user_service)):
    return service.add(user_data.to_model())

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