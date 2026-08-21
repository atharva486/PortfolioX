import pytest
from decimal import Decimal
from app.domain.asset import Stock
from app.domain.order import MarketOrder, LimitOrder, OrderType, InvalidOrderError

@pytest.fixture
def sample_stock():
    # Pytest fixtures let us reuse this object in multiple tests!
    return Stock("Apple", "AAPL",  "Tech")

def test_order_quantity_validation(sample_stock):
    """PORTX-2: Ensure zero or negative quantities raise InvalidOrderError."""
    with pytest.raises(InvalidOrderError, match="Quantity must be a positive integer"):
        MarketOrder(sample_stock, 0, OrderType.BUY)
        
    with pytest.raises(InvalidOrderError):
        MarketOrder(sample_stock, -5, OrderType.SELL)

def test_market_order_execution(sample_stock):
    """Market orders should always be ready to execute."""
    order = MarketOrder(sample_stock, 10, OrderType.BUY)
    assert order.can_execute(Decimal("160.00")) is True
    assert order.can_execute(Decimal("10.00")) is True

def test_limit_order_buy_logic(sample_stock):
    """Limit BUY: only execute if market price is <= limit price."""
    order = LimitOrder(sample_stock, 10, OrderType.BUY, limit_price=Decimal("150.00"))
    
    # Market drops to 149 - Execute!
    assert order.can_execute(Decimal("149.00")) is True
    # Market exactly at 150 - Execute!
    assert order.can_execute(Decimal("150.00")) is True
    # Market goes up to 151 - Do NOT execute
    assert order.can_execute(Decimal("151.00")) is False

def test_limit_order_sell_logic(sample_stock):
    """Limit SELL: only execute if market price is >= limit price."""
    order = LimitOrder(sample_stock, 10, OrderType.SELL, limit_price=Decimal("150.00"))
    
    # Market drops to 149 - Do NOT execute
    assert order.can_execute(Decimal("149.00")) is False
    # Market exactly at 150 - Execute!
    assert order.can_execute(Decimal("150.00")) is True
    # Market goes up to 151 - Execute!
    assert order.can_execute(Decimal("151.00")) is True