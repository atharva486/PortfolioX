
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.domain.account import Account
from app.models.account_model import AccountModel

class AccountRepository:
    def __init__(self,session : Session):
        self.session = session

    def create_account(self,balance:Decimal):
        account_db = AccountModel(balance=balance)
        self.session.add(account_db)
        self.session.commit()
        self.session.refresh(account_db)
        return account_db

    def get_account(self,account_id:int):
        return self.session.query(AccountModel).filter(AccountModel.id == account_id).first()

    def get_all_accounts(self):
        return self.session.query(AccountModel).all()
    