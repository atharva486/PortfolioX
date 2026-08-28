from fastapi import APIRouter,Depends,HTTPException
from app.db.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.account_schema import CreateAccountRequest,AccountResponse
from app.repositories.account_repository import AccountRepository

router = APIRouter()

@router.post("/accounts")
def create_account(account:CreateAccountRequest, db:Session=Depends(get_db)):
    data_db = account.model_dump()
    account1 = AccountRepository(session=db)
    new_account = account1.create_account(balance = data_db["balance"])
    return new_account

@router.get('/accounts/{account_id}',response_model=AccountResponse)
def get_account(account_id:int,db:Session = Depends(get_db)):
    account1 = AccountRepository(session=db)
    account = account1.get_account(account_id=account_id)
    if account is None:
        raise HTTPException(status_code=404,detail="Account not found")
    return account






