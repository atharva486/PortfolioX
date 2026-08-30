from decimal import Decimal
from typing import cast

from sqlalchemy.orm import Session
from app.domain.account import Account
from app.models.account_model import AccountModel
from app.domain.asset import Asset,Stock,Bond,AssetType
from app.models.asset_model import AssetModel
from app.models.holding_model import HoldingModel
from app.repositories.account_repository import AccountRepository
from app.domain.order import OrderSide,LimitOrder,MarketOrder,OrderType

class AssetRepository:
    def __init__(self,session:Session):
        self.session=session

    def get_asset(self,symbol:str)->Asset|None:
        asset = self.session.query(AssetModel).filter(AssetModel.symbol == symbol).first()
        if not asset:
            return None
        if cast(AssetType,asset.asset_type) == AssetType.STOCK:
            return Stock(cast(str, asset.company_name), cast(str, asset.symbol), sector=cast(str,asset.sector))
        else:
            return Bond(symbol=cast(str, asset.symbol), name=cast(str, asset.company_name),coupon_rate=cast(Decimal,asset.coupon_rate))
        