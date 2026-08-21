import pytest
from decimal import Decimal
from app.domain.account import Account
from app.domain.portfolio import Portfolio
from app.domain.exceptions import MissingPriceError

@pytest.fixture
def populated_account():
    # Setup an account with $5,000 cash and some existing stock
    acc = Account(balance=Decimal("5000.00"))
    acc.holdings = {
        "AAPL": {"quantity": 10, "avg_price": Decimal("150.00")}, # Cost basis: $1500
        "TSLA": {"quantity": 5, "avg_price": Decimal("200.00")}   # Cost basis: $1000
    }
    return acc

def test_total_portfolio_value(populated_account):
    """PORTX-4: Should calculate cash + live value of all assets."""
    portfolio = Portfolio(populated_account)
    live_prices = {
        "AAPL": Decimal("160.00"), # 10 * 160 = $1600
        "TSLA": Decimal("190.00")  # 5 * 190 = $950
    }
    
    # 5000 cash + 1600 AAPL + 950 TSLA = 7550
    assert portfolio.total_value(live_prices) == Decimal("7550.00")

def test_unrealized_pnl(populated_account):
    """PORTX-4: Should calculate total profit/loss across all holdings."""
    portfolio = Portfolio(populated_account)
    live_prices = {
        "AAPL": Decimal("160.00"), # Up $10 per share * 10 = +$100
        "TSLA": Decimal("190.00")  # Down $10 per share * 5 = -$50
    }
    
    # +100 - 50 = +50 P&L
    assert portfolio.unrealized_pnl(live_prices) == Decimal("50.00")

def test_missing_price_raises_error(populated_account):
    """Ensure missing market data fails fast."""
    portfolio = Portfolio(populated_account)
    # TSLA is missing from the live prices!
    bad_live_prices = {"AAPL": Decimal("160.00")}
    
    with pytest.raises(MissingPriceError, match="Live price for TSLA is not available"):
        portfolio.total_value(bad_live_prices)