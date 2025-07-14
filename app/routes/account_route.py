from fastapi import APIRouter, Depends
from app.dependencies.user_dependencies import get_current_user
from app.services.account_service import AccountService
from app.dependencies.account_dependencies import get_account_service
from app.schemas.account_schemas import AccountCreate, AccountBase
from app.entities.user import User

router = APIRouter()



@router.get("", response_model=list[AccountBase])
def read_accounts_list(service: AccountService = Depends(get_account_service), current_user: User = Depends(get_current_user)):
    """
    Get a list of all accounts.
    
    This endpoint requires authentication via JWT token.
    Include the token in the Authorization header as: `Bearer <your_token>`
    """
    return service.get_by_user_id(current_user.id)

@router.post("", response_model=AccountBase,
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