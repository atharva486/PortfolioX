from pydantic import BaseModel,Field
from decimal import Decimal
from enum import Enum
from app.domain.order import OrderType,OrderSide

    
class AssetType(str, Enum):
    STOCK = "STOCK"
    BOND = "BOND"

class OrderCreate(BaseModel):
    symbol:str
    asset_type:AssetType
    quantity:int = Field(gt=0,description="Quantity must be present")
    order_type:OrderType
    live_price: Decimal = Field(gt=0, description="Temporary: fake live market price")
    side:OrderSide # market or limit order
    limit_price:Decimal|None =None

class OrderResponse(BaseModel):
    status:str
    new_balance:Decimal
    filled_price:Decimal|None

