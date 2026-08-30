import pytest
from decimal import Decimal
from app.domain.account import Account
from app.domain.asset import Stock
from app.domain.order import MarketOrder, LimitOrder, OrderSide
from app.domain.exceptions import InsufficientFundsError, InsufficientHoldingsError

@pytest.fixture
def sample_stock():
    return Stock("Apple", "AAPL", "Tech")

@pytest.fixture
def empty_account():
    return Account(balance=Decimal("1000.00"),id=1)

def test_successful_buy_order(empty_account, sample_stock):
    """Test buying a stock updates balance and holdings."""
    order = MarketOrder(sample_stock, 2, OrderSide.BUY)
    result = empty_account.place_order(order, Decimal("150.00"))
    
    assert empty_account.balance == Decimal("700.00")  # 1000 - (2 * 150)
    assert empty_account.holdings["AAPL"]["quantity"] == 2
    assert empty_account.holdings["AAPL"]["avg_price"] == Decimal("150.00")
    assert empty_account.id == 1

def test_insufficient_funds(empty_account, sample_stock):
    """Test buying without enough cash raises an error."""
    order = MarketOrder(sample_stock, 10, OrderSide.BUY) # Costs $1500, only have $1000
    with pytest.raises(InsufficientFundsError):
        empty_account.place_order(order, Decimal("150.00"))
        
    # Ensure state was not mutated (Atomicity!)
    assert empty_account.balance == Decimal("1000.00")
    assert "AAPL" not in empty_account.holdings
    assert empty_account.id == 1

def test_successful_sell_order(empty_account, sample_stock):
    """Test selling a stock updates balance and reduces holdings."""
    # Setup: Give them shares first
    empty_account.holdings["AAPL"] = {"quantity": 5, "avg_price": Decimal("100.00")}
    empty_account.balance = Decimal("0.00")
    
    order = MarketOrder(sample_stock,2, OrderSide.SELL)
    empty_account.place_order(order, Decimal("200.00")) # Sell 2 at $200 = +$400
    
    assert empty_account.balance == Decimal("400.00")
    assert empty_account.id == 1
    assert empty_account.holdings["AAPL"]["quantity"] == 3

def test_pending_limit_order(empty_account, sample_stock):
    """Test that a limit order that cannot execute returns Pending."""
    order = LimitOrder(sample_stock, 2, OrderSide.BUY, limit_price=Decimal("140.00"))
    result = empty_account.place_order(order, Decimal("150.00")) # Market price too high
    
    assert empty_account.balance == Decimal("1000.00") # No money spent
    assert empty_account.id == 1