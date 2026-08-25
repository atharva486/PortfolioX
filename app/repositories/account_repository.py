
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.domain.account import Account
from app.models.account_model import AccountModel
from app.domain.asset import Asset,Stock,Bond
from app.models.asset_model import AssetModel


class AccountRepository:

    
    def __init__(self,session : Session):
        self.session = session


    def stock_or_bond(self,asset:AssetModel):
        if asset.asset_type == "BOND":
            return Bond(
                symbol=asset.symbol,
                name=asset.company_name,
                coupon_rate=Decimal("0.0")
            )
        else:
            return Stock(
                symbol=asset.symbol,
                name=asset.company_name,
                sector="Unknown"
            )

    def create_account(self,balance:Decimal)->AccountModel:
        account_db = AccountModel(balance=balance)
        self.session.add(account_db)
        self.session.commit()
        self.session.refresh(account_db)
        return account_db

    def get_account(self,account_id:int)->AccountModel:
        return self.session.query(AccountModel).filter(AccountModel.id == account_id).first()

    def get_all_accounts(self)->list[AccountModel]:
        return self.session.query(AccountModel).all()

    def  _to_domain(self,account:AccountModel)->Account:
        if account is not None:
            domain_account = Account(balance =Decimal(str(account.balance)),id = account.id)
            holdings={}
            for holding in account.holdings:
                asset_val = self.stock_or_bond(holding.asset)
                holdings[holding.symbol] = {
                    "quantity" : holding.quantity,
                    "avg_price" : holding.avg_price,
                    "asset" : asset_val
                }
            domain_account.holdings = holdings
            return domain_account

    def get_domain_account(self,account_id:int)->Account:
        raw_account  = self.get_account(account_id = account_id)
        return self._to_domain(account=raw_account)
