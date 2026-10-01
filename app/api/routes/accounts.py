from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.account_repository import AccountRepository
from app.schemas.account_schema import AccountResponse, CreateAccountRequest

router = APIRouter(tags=["Accounts"])


@router.post("/accounts", response_model=AccountResponse, status_code=201)
def create_account(
    account: CreateAccountRequest, db: Session = Depends(get_db)
) -> AccountResponse:
    repo = AccountRepository(session=db)
    created = repo.create_account(balance=account.balance)
    return AccountResponse.model_validate(created)


@router.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)) -> AccountResponse:
    repo = AccountRepository(session=db)
    # Read path: no row lock. Locking is opt-in via for_update=True.
    found = repo.get_account(account_id=account_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse.model_validate(found)
