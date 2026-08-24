import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.account_model import AccountModel
from app.models.holding_model import HoldingModel
from app.models.asset_model import AssetModel

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