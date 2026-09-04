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

    def save(self, asset: Asset) -> None:
        """Saves a new domain Asset into the database."""
        # Check if it already exists to avoid duplicate key errors
        existing = self.session.query(AssetModel).filter_by(symbol=asset.symbol).first()
        if existing:
            return

        new_asset_model = AssetModel(
            symbol=asset.symbol,
            company_name=asset.name,
            asset_type=asset.asset_type.name, # Save the enum string
            sector=getattr(asset, 'sector', None),
            coupon_rate=getattr(asset, 'coupon_rate', None)
        )
        self.session.add(new_asset_model)
        self.session.commit()