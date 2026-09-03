from decimal import Decimal
from pydantic import BaseModel
from app.domain.asset import AssetType  # Import your actual domain Enum

class AssetSearchRequest(BaseModel):
    symbol: str
    name: str
    asset_type: AssetType
    sector: str | None = None
    coupon_rate: Decimal | None = None