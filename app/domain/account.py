from dataclasses import dataclass
from decimal import Decimal

from app.domain.asset import Asset
from app.domain.exceptions import InsufficientFundsError, InsufficientHoldingsError
from app.domain.order import Order, OrderSide


@dataclass
class Position:
    """A single holding in an account.

    This was previously an untyped dict with string keys
    ({"quantity": ..., "avg_price": ..., "asset": ...}). A dict with
    heterogeneous values cannot be type-checked, cannot be
    autocompleted, and forced defensive `hasattr` branching in the
    repository layer. A dataclass makes the shape explicit.
    """

    quantity: Decimal
    avg_price: Decimal
    asset: Asset


class Account:
    def __init__(self, balance: Decimal, id: int):
        self.id = id
        self.balance = balance
        self.holdings: dict[str, Position] = {}

    def place_order(self, order: Order, current_market_price: Decimal) -> bool:
        if not order.can_execute(current_market_price):
            return False

        symbol = order.asset.symbol
        total_cost = order.quantity * current_market_price

        if order.order_side == OrderSide.BUY:
            if total_cost > self.balance:
                raise InsufficientFundsError("Insufficient funds to execute the order.")

            self.balance -= total_cost
            existing = self.holdings.get(symbol)

            if existing is not None:
                # Weighted-average cost basis across both lots.
                total_quantity = existing.quantity + Decimal(order.quantity)
                existing.avg_price = (
                    existing.avg_price * existing.quantity
                    + current_market_price * Decimal(order.quantity)
                ) / total_quantity
                existing.quantity = total_quantity
            else:
                self.holdings[symbol] = Position(
                    quantity=Decimal(order.quantity),
                    avg_price=Decimal(current_market_price),
                    asset=order.asset,
                )

        elif order.order_side == OrderSide.SELL:
            existing = self.holdings.get(symbol)
            if existing is None or existing.quantity < Decimal(order.quantity):
                raise InsufficientHoldingsError(
                    "Insufficient holdings to execute the sell order."
                )

            self.balance += total_cost
            existing.quantity -= Decimal(order.quantity)
            if existing.quantity == 0:
                del self.holdings[symbol]

        return True
