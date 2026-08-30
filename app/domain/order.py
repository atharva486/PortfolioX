from abc import ABC, abstractmethod
from enum import Enum
from decimal import Decimal

from app.domain.asset import Asset
from app.domain.exceptions import InvalidOrderError


class OrderSide(Enum):
    BUY = "Buy"
    SELL = "Sell"


class OrderType(Enum):
    MARKET = "Market"
    LIMIT = "Limit"


class Order(ABC):
    def __init__(self, asset: Asset, quantity: int, order_side: OrderSide):
        self.asset = asset
        if quantity <= 0:
            raise InvalidOrderError("Quantity must be a positive integer.")
        self.quantity = quantity
        self.order_side = order_side

    @property
    @abstractmethod
    def order_type(self) -> OrderType:
        pass

    @abstractmethod
    def can_execute(self, current_market_price: Decimal) -> bool:
        pass


class MarketOrder(Order):
    def __init__(self, asset: Asset, quantity: int, order_side: OrderSide):
        super().__init__(asset, quantity, order_side)

    @property
    def order_type(self) -> OrderType:
        return OrderType.MARKET

    def can_execute(self, current_market_price: Decimal) -> bool:
        return True


class LimitOrder(Order):
    def __init__(self, asset: Asset, quantity: int, order_side: OrderSide, limit_price: Decimal):
        super().__init__(asset, quantity, order_side)
        self._limit_price = limit_price

    @property
    def order_type(self) -> OrderType:
        return OrderType.LIMIT

    def can_execute(self, current_market_price: Decimal) -> bool:
        if self.order_side == OrderSide.BUY:
            return current_market_price <= self._limit_price
        elif self.order_side == OrderSide.SELL:
            return current_market_price >= self._limit_price
        else:
            raise InvalidOrderError("Invalid order type.")

    