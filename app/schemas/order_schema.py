from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Side(int, Enum):
    BUY = 0
    SELL = 1


class Type(int, Enum):
    MARKET = 0
    LIMIT = 1


class OrderStatus(str, Enum):
    FILLED = "FILLED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class OrderCreate(BaseModel):
    symbol: str
    quantity: int = Field(gt=0, description="Quantity must be present")
    order_type: Type
    side: Side  # market or limit order
    limit_price: Decimal | None = None

    @model_validator(mode="after")
    def validate_limit_price(self) -> "OrderCreate":
        """A LIMIT order without a limit price is invalid.

        Previously this combination silently fell through to a
        MarketOrder inside OrderRepository.create_order(), so a user
        asking for a price cap was filled at any price. Rejecting it at
        the boundary makes that failure mode unrepresentable.
        """
        if self.order_type is Type.LIMIT:
            if self.limit_price is None:
                raise ValueError("limit_price is required for LIMIT orders")
            if self.limit_price <= 0:
                raise ValueError("limit_price must be greater than zero")
        elif self.limit_price is not None:
            raise ValueError("limit_price is only valid for LIMIT orders")
        return self


class OrderResponse(BaseModel):
    status: OrderStatus
    new_balance: Decimal
    filled_price: Decimal | None = None
    order_id: int | None = None
