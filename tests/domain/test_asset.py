import pytest
from decimal import Decimal
from app.domain.asset import Asset, Stock, Bond, AssetType

def test_cannot_instantiate_base_asset():
    """PORTX-1: Verify that the abstract base class cannot be instantiated."""
    with pytest.raises(TypeError):
        # This will fail because Asset has abstract methods
        Asset()

def test_stock_initialization_and_properties():
    """Verify Stock correctly sets and returns all properties."""
    stock = Stock(
        name="Apple Inc.", 
        symbol="AAPL", 
        current_price=Decimal("150.00"), 
        sector="Technology"
    )
    
    assert stock.name == "Apple Inc."
    assert stock.symbol == "AAPL"
    assert stock.current_price == Decimal("150.00")
    assert stock.sector == "Technology"
    assert stock.asset_type == AssetType.STOCK

def test_bond_initialization_and_properties():
    """Verify Bond correctly sets and returns all properties."""
    bond = Bond(
        name="US Treasury 10Y", 
        symbol="UST10Y", 
        current_price=Decimal("980.50"), 
        coupon_rate=Decimal("0.045")
    )
    
    assert bond.name == "US Treasury 10Y"
    assert bond.symbol == "UST10Y"
    assert bond.current_price == Decimal("980.50")
    assert bond.coupon_rate == Decimal("0.045")
    assert bond.asset_type == AssetType.BOND

def test_price_setter_validation():
    """Verify that price updates work, but negative prices raise a ValueError."""
    stock = Stock("Tesla", "TSLA", Decimal("200.00"), "Auto")
    
    # Valid update
    stock.current_price = Decimal("210.00")
    assert stock.current_price == Decimal("210.00")
    
    # Invalid update
    with pytest.raises(ValueError, match="Price must be a positive value"):
        stock.current_price = Decimal("-10.00")