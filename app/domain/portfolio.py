from app.domain.account import Account
from decimal import Decimal
from app.domain.exceptions import MissingPriceError

class Portfolio():
    def __init__ (self,account:Account):
        self.account=account

    def total_value(self,live_prices:dict)->Decimal:
        total_value = self.account.balance
        for symbol, asset_data in self.account.holdings.items():
            quantity = asset_data["quantity"]
            if symbol in live_prices:
                total_value += quantity * live_prices[symbol]
            else:
                raise MissingPriceError(f"Live price for {symbol} is not available.")
        return total_value

    def unrealized_pnl(self,live_prices:dict)->Decimal:
        total_pnl = Decimal(0)
        for symbol, asset_data in self.account.holdings.items():
            quantity = asset_data["quantity"]
            avg_price = asset_data["avg_price"]
            if symbol in live_prices:
                current_price = live_prices[symbol]
                pnl = (current_price - avg_price) * quantity
                total_pnl += pnl
            else:
                raise MissingPriceError(f"Live price for {symbol} is not available.")
        return total_pnl

    