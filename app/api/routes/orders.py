from app.services.market_data_services import MarketDataService
from fastapi import APIRouter,Depends,HTTPException
from app.db.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.account_schema import CreateAccountRequest,AccountResponse
from app.repositories.account_repository import AccountRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order_schema import OrderCreate,OrderResponse
from app.domain.exceptions import InsufficientFundsError, InsufficientHoldingsError
from app.repositories.asset_repository import AssetRepository
from app.domain.asset import AssetType,Stock,Bond
from app.domain.order import OrderSide, OrderType
from decimal import Decimal

router = APIRouter(tags=["Orders"])


@router.post('/accounts/{account_id}/orders/{symbol}/{order_side}/{order_type}/{quantity}', response_model=OrderResponse)
async def place_order_endpoint(
    account_id: int,
    symbol: str,
    order_side: int,   # 0 = BUY, 1 = SELL
    order_type: int,   # 0 = MARKET, 1 = LIMIT
    quantity: int,
    db: Session = Depends(get_db),
    limit_price: Decimal | None = None
):
    # Map int flags → domain enums
    side = OrderSide.BUY if order_side == 0 else OrderSide.SELL
    otype = OrderType.MARKET if order_type == 0 else OrderType.LIMIT

    order_repo = OrderRepository(db)
    asset_repo = AssetRepository(db)
    market_service = MarketDataService()
    
    # 1. Fetch live price
    live_price = await market_service.get_price(symbol)
    if live_price is None:
        raise HTTPException(status_code=404, detail="Live price not found for the given symbol")

    # 2. Just-In-Time Asset Creation (If missing from DB)
    asset = asset_repo.get_asset(symbol)
    if not asset:
        # Search Finnhub for the missing asset details
        search_results = await market_service.search_assets(symbol)
        
        # Find the exact symbol match
        exact_match = next((res for res in search_results if res.symbol.upper() == symbol.upper()), None)
        if not exact_match:
            raise HTTPException(status_code=404, detail=f"Asset {symbol} does not exist in market data.")
            
        # Build the domain entity and save it to the DB
        if exact_match.asset_type == AssetType.STOCK:
            new_asset = Stock(name=exact_match.name, symbol=exact_match.symbol, sector=exact_match.sector or "Unknown")
        else:
            new_asset = Bond(name=exact_match.name, symbol=exact_match.symbol, coupon_rate=Decimal("5.0"))
            
        asset_repo.save(new_asset)

    # 3. Place the actual order
    try:
        result = order_repo.place_order(
            live_price=live_price,
            symbol=symbol,
            account_id=account_id,
            order_side=side,
            limit_price=limit_price,
            order_type=otype,
            quantity=quantity
        )
        
        if result is None:
            raise HTTPException(status_code=404, detail="Account not found")
            
        return result
        
    except (InsufficientFundsError, InsufficientHoldingsError) as e:
        raise HTTPException(status_code=400, detail=str(e))