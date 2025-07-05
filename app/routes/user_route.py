from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.dependencies.user_dependencies import get_user_service
from app.schemas.user_schemas import UserCreate, UserBase


router = APIRouter()

@router.get("")
async def read_users_list(service: UserService = Depends(get_user_service)):
    return service.get_all()

@router.post("", response_model=UserBase)
async def create_user(user_data: UserCreate, service: UserService = Depends(get_user_service)):
    return service.add(user_data.to_model())