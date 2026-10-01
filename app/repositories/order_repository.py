from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.asset import Asset
from app.domain.order import LimitOrder, MarketOrder, Order, OrderSide, OrderType
from app.repositories.account_repository import AccountRepository
from app.repositories.asset_repository import AssetRepository


@dataclass
class OrderOutcome:
    """Result of an execution attempt. Typed instead of a bare dict so
    callers cannot silently read a missing key."""

    filled: bool
    new_balance: Decimal
    filled_price: Decimal | None


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_order(
        self,
        order_type: OrderType,
        quantity: int,
        order_side: OrderSide,
        limit_price: Decimal | None,
        asset: Asset,
    ) -> Order:
        # NOTE (ADR pending): a LIMIT order with limit_price=None silently
        # falls through to a MarketOrder here. That should be rejected at the
        # API boundary instead — see app/schemas/order_schema.py.
        if order_type == OrderType.LIMIT and limit_price is not None:
            return LimitOrder(asset, quantity, order_side, limit_price)
        else:
            return MarketOrder(asset, quantity, order_side)

    def place_order(
        self,
        live_price: Decimal,
        symbol: str,
        account_id: int,
        order_side: OrderSide,
        limit_price: Decimal | None,
        order_type: OrderType,
        quantity: int,
    ) -> OrderOutcome | None:
        account_repo = AccountRepository(self.session)
        asset_repo = AssetRepository(self.session)

        account = account_repo.get_domain_account(account_id)
        if account is None:
            return None

        asset = asset_repo.get_asset(symbol)
        if asset is None:
            return None

        order = self.create_order(order_type, quantity, order_side, limit_price, asset)
        filled = account.place_order(order, live_price)
        account_repo.save(account)

        return OrderOutcome(
            filled=filled,
            new_balance=account.balance,
            filled_price=live_price if filled else None,
        )
