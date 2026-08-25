import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.asset import Stock
from app.models.account_model import AccountModel
from app.models.holding_model import HoldingModel
from app.models.asset_model import AssetModel

from app.domain.order import MarketOrder
from app.domain.order import OrderType

# Import your Base so we can create tables in memory!
from app.models.base import Base # Adjust this import if your Base is somewhere else
from app.repositories.account_repository import AccountRepository

# 1. THE FIXTURE: This runs before every single test
@pytest.fixture
def db_session():
    # Create an engine that only lives in RAM
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    
    # Build all the tables in the RAM database
    Base.metadata.create_all(engine)
    
    # Create a fresh session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session  # Pause here and hand the session to the test
    
    # Once the test is done, close it and throw the RAM database away
    session.close()

# 2. THE TESTS
def test_create_account(db_session):
    # Setup
    repo = AccountRepository(db_session)
    
    # Action
    account = repo.create_account(balance=Decimal("5000.00"))
    
    # Assertion (Did it work?)
    assert account.id is not None # The DB should have generated an ID
    assert account.balance == Decimal("5000.00")

def test_get_account(db_session):
    # Setup
    repo = AccountRepository(db_session)
    new_account = repo.create_account(balance=Decimal("1500.00"))
    
    # Action
    fetched_account = repo.get_account(new_account.id)
    
    # Assertion
    assert fetched_account is not None
    assert fetched_account.id == new_account.id
    assert fetched_account.balance == Decimal("1500.00")


def test_get_domain_account_and_place_order(db_session):
    # 1. SETUP: Put some raw data in the database
    repo = AccountRepository(db_session)
    
    db_account = repo.create_account(balance=Decimal("10000.00"))
    
    apple_asset = AssetModel(symbol="AAPL", asset_type="STOCK", company_name="Apple Inc.")
    db_session.add(apple_asset)
    db_session.commit()
    
    holding = HoldingModel(
        account_id=db_account.id, 
        symbol="AAPL", 
        quantity=Decimal("10"), 
        avg_price=Decimal("150.00")
    )
    db_session.add(holding)
    db_session.commit()

    # 2. THE TEST: Fetch the domain account
    domain_account = repo.get_domain_account(db_account.id)

    assert domain_account is not None
    assert domain_account.balance == Decimal("10000.00")
    assert "AAPL" in domain_account.holdings
    
    # 3. THE ULTIMATE TEST: Use MarketOrder
    new_apple_stock = Stock(symbol="AAPL", name="Apple Inc.", sector="Tech")
    
    # ✅ Create a MarketOrder instead of the abstract Order
    buy_order = MarketOrder(
        asset=new_apple_stock, 
        quantity=Decimal("5"), 
        order_type=OrderType.BUY
    )
    
    # Pass the MarketOrder into your method
    result = domain_account.place_order(order=buy_order, current_market_price=Decimal("160.00"))
    
    # 4. ASSERTIONS: Did the math work?
    assert "Order executed" in result
    assert domain_account.balance == Decimal("9200.00") # 10000 - (5 * 160)
    assert domain_account.holdings["AAPL"]["quantity"] == Decimal("15")

    print("\n✅ THE MAPPER WORKS! Domain Logic successfully ran on Database Data.")