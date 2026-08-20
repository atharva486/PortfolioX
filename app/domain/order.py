from abc import ABC, abstractmethod
from enum import Enum
from app.domain.asset import Asset, AssetType
from decimal import Decimal

class InvalidOrderError(Exception):
    """Custom exception for invalid order types."""
    pass

class OrderType(Enum):
    BUY = "Buy"
    SELL = "Sell"

class Order(ABC):
    def __init__(self,asset:Asset,quantity:int,order_type:OrderType ):
        self.asset = asset
        if quantity <= 0:
            raise InvalidOrderError("Quantity must be a positive integer.")
        self.quantity = quantity
        self.order_type = order_type

    @abstractmethod
    def can_execute(self,current_market_price)->bool:
        pass

class MarketOrder(Order):
    def __init__(self,asset:Asset,quantity:int,order_type:OrderType):
        super().__init__(asset,quantity,order_type)

    def can_execute(self,current_market_price:Decimal)->bool:
        return True

class LimitOrder(Order):
    def __init__(self,asset:Asset,quantity:int,order_type:OrderType,limit_price:Decimal):
        super().__init__(asset,quantity,order_type)
        self._limit_price = limit_price

    def can_execute(self,current_market_price:Decimal)->bool:
        if self.order_type ==OrderType.BUY:
            return current_market_price <= self._limit_price
        elif self.order_type == OrderType.SELL:
            return current_market_price >= self._limit_price
        else:
            raise InvalidOrderError("Invalid order type.")

    