from decimal import Decimal

from app.domain.account import Account
from app.domain.exceptions import MissingPriceError


class Portfolio:
    """Valuation logic over an Account, driven by live prices.

    NOTE: this class was previously dead code. `app/api/routes/portfolio.py`
    reimplemented the same maths inline and computed `total_value` from
    `avg_price` (cost basis) while omitting cash entirely. The routes now
    delegate here, so the numbers are computed in exactly one place.
    """

    def __init__(self, account: Account) -> None:
        self.account = account

    def total_value(self, live_prices: dict[str, Decimal]) -> Decimal:
        """Cash plus the market value of every holding.

        A missing price raises rather than defaulting to zero: a silent
        zero would report a fabricated 100% loss.
        """
        total_value = self.account.balance
        for symbol, position in self.account.holdings.items():
            price = self._price_for(symbol, live_prices)
            total_value += position.quantity * price
        return total_value

    def unrealized_pnl(self, live_prices: dict[str, Decimal]) -> Decimal:
        """Mark-to-market profit/loss on open positions (excludes cash)."""
        total_pnl = Decimal("0.00")
        for symbol, position in self.account.holdings.items():
            price = self._price_for(symbol, live_prices)
            total_pnl += (price - position.avg_price) * position.quantity
        return total_pnl

    def _price_for(self, symbol: str, live_prices: dict[str, Decimal]) -> Decimal:
        if symbol not in live_prices:
            raise MissingPriceError(f"Live price for {symbol} is not available.")
        return live_prices[symbol]
