
from decimal import Decimal
from typing import cast

from sqlalchemy.orm import Session
from app.domain.account import Account
from app.models.account_model import AccountModel
from app.domain.asset import Asset,Stock,Bond
from app.models.asset_model import AssetModel
from app.models.holding_model import HoldingModel


class AccountRepository:
    
    def __init__(self,session : Session):
        self.session = session


    def stock_or_bond(self,asset:AssetModel):
        asset_type = cast(str, asset.asset_type)
        if asset_type == "BOND":
            return Bond(
                symbol=cast(str, asset.symbol),
                name=cast(str, asset.company_name),
                coupon_rate=Decimal("0.0")
            )
        else:
            return Stock(
                symbol=cast(str, asset.symbol),
                name=cast(str, asset.company_name),
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

    def  _to_domain(self,account:AccountModel)->Account|None:
        if account is not None:
            domain_account = Account(balance =Decimal(str(account.balance)),id = cast(int, account.id))
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
        return None

    def get_domain_account(self,account_id:int)->Account|None:
        raw_account  = self.get_account(account_id = account_id)
        return self._to_domain(account=raw_account)

    def save(self,domain_account:Account):
        account = self.get_account(domain_account.id)
        if not account:
            return None
        account.balance =domain_account.balance
        # 3. Update or Insert Holdings
        for symbol, holding in domain_account.holdings.items():
            # Safely extract quantity and avg_price whether your domain uses dicts or objects
            quantity = holding.quantity if hasattr(holding, 'quantity') else holding.get('quantity', 0)
            avg_price = holding.avg_price if hasattr(holding, 'avg_price') else holding.get('avg_price', Decimal("0.0"))

            # Check if this holding already exists in the database
            holding_model = self.session.query(HoldingModel).filter(
                HoldingModel.account_id == domain_account.id,
                HoldingModel.symbol == symbol
            ).first()

            if holding_model:
                # Update existing holding
                holding_model.quantity = quantity
                holding_model.avg_price = avg_price
            else:
                # Insert brand new holding
                new_holding = HoldingModel(
                    account_id=domain_account.id,
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=avg_price
                )
                self.session.add(new_holding)

        # 4. Save everything to PostgreS
        self.session.commit()


