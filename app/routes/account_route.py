from fastapi import APIRouter, Depends, status
import app
from app.dependencies.user_dependencies import get_current_user
from app.schemas.base_schemas import SearchResponse
from app.services.account_service import AccountService
from app.dependencies.account_dependencies import get_account_service
from app.schemas.account_schemas import AccountCreate, AccountResponse, AccountUpdate
from app.entities.user import User
from uuid import UUID


router = APIRouter()



@router.get("", response_model=SearchResponse[AccountResponse])
def read_accounts_list(service: AccountService = Depends(get_account_service), current_user: User = Depends(get_current_user)):
    """
    Get a list of all accounts.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get_by_user_id(current_user.id)


@router.get("/{account_id}", response_model=AccountResponse, dependencies=[Depends(get_current_user)])
def read_account(account_id: UUID, service: AccountService = Depends(get_account_service)):
    """
    Get a specific account by ID.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get(account_id)

@router.post("", response_model=AccountResponse,
             summary="Create a new account",
             description="Create a new account with the provided data. Requires a valid JWT token in the Authorization header.")
async def create_account(
    account_data: AccountCreate, 
    service: AccountService = Depends(get_account_service), 
    current_user: User = Depends(get_current_user)):
    """
    Create a new account.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    print(current_user.id)
    return service.add(account_data.to_model(current_user.id))


@router.put("/{account_id}", response_model=AccountResponse,
             summary="Update an account",
             description="Update an account with the provided data. Requires a valid JWT token in the Authorization header.")
async def update_account(
    account_id: UUID,
    account_data: AccountUpdate,
    service: AccountService = Depends(get_account_service), 
    current_user: User = Depends(get_current_user)):
    """
    Update an account.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.update(account_id, account_data, user_id=current_user.id)

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    service: AccountService = Depends(get_account_service), 
    current_user: User = Depends(get_current_user)):
    """
    Delete an account.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.delete(account_id, user_id=current_user.id)