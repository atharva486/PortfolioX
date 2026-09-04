from pydantic import BaseModel,Field
from decimal import Decimal
from enum import Enum
from app.domain.asset import AssetType


class Side(int, Enum):
    BUY = 0
    SELL = 1

class Type(int, Enum):
    MARKET = 0
    LIMIT = 1

class OrderCreate(BaseModel):
    symbol:str
    quantity:int = Field(gt=0,description="Quantity must be present")
    order_type:Type
    side:Side # market or limit order
    limit_price:Decimal|None =None

class OrderResponse(BaseModel):
    status:str
    new_balance:Decimal
    filled_price:Decimal|None
