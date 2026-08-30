
from decimal import Decimal
from typing import cast

from sqlalchemy.orm import Session
from app.domain.account import Account
from app.models.account_model import AccountModel
from app.domain.asset import Asset,Stock,Bond
from app.models.asset_model import AssetModel
from app.models.holding_model import HoldingModel
from app.repositories.account_repository import AccountRepository
from app.domain.order import OrderSide,LimitOrder,MarketOrder,OrderType
from app.repositories.asset_repository import AssetRepository

class OrderRepository:
    def __init__(self,session:Session):
        self.session =session

    def create_order(self,order_type:OrderType,quantity:int,order_side:OrderSide,limit_price:Decimal|None,asset:Asset):
        if order_type == OrderType.LIMIT.value and limit_price is not None:
            return LimitOrder(asset,quantity,order_side,limit_price)
        else:
            return MarketOrder(asset,quantity,order_side)

    def place_order(self,live_price:Decimal,symbol:str,account_id:int,order_side:OrderSide,limit_price:Decimal|None,order_type:OrderType,quantity:int)->dict|None:
        accountRepo =AccountRepository(self.session)
        assetRepo = AssetRepository(self.session)
        account = accountRepo.get_domain_account(account_id)
        if account is not None:
            if assetRepo is not None:
                asset = assetRepo.get_asset(symbol)
                if asset is not None:
                    order = self.create_order(order_type,quantity,order_side,limit_price,asset)
                    trade_success = account.place_order(order,live_price)   
                    accountRepo.save(account)
                    return {
                    "status": "FILLED" if trade_success else "FAILED",
                    "new_balance": account.balance,
                    "filled_price": live_price if trade_success else None
                    }
        return None