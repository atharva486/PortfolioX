from app.schemas.account_schema import AccountResponse
from app.schemas.portfolio_schema import PortfolioSummaryResponse,HoldingSchema
from fastapi import APIRouter,Depends,HTTPException
from app.db.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal
from app.repositories.account_repository import AccountRepository
from app.services.market_data_services import MarketDataService

router = APIRouter(tags=['Holdings'])

@router.get('/accounts/{account_id}/portfolio',response_model = PortfolioSummaryResponse)
async def get_portfolio(account_id:int,db:Session = Depends(get_db))->PortfolioSummaryResponse:
    market = MarketDataService()
    account_repo = AccountRepository(db)
    account =account_repo.get_domain_account(account_id)
    if account is not None:
        id = account.id
        balance = account.balance
        holdings = []
        total_pnl = Decimal("0.00")
        
        # Batch fetch all prices concurrently
        symbols_to_fetch = list(account.holdings.keys())
        live_prices = await market.get_prices(symbols_to_fetch)
        
        for symbol, data in account.holdings.items():
            live_price = live_prices.get(symbol, Decimal("0.00"))
            quantity = data.get("quantity", 0)
            avg_price = data.get("avg_price", Decimal("0.00"))
            
            holdings.append(HoldingSchema(
                symbol=symbol,
                quantity=quantity,
                avg_price=avg_price,
                live_price=live_price
            ))
            total_pnl += (live_price - Decimal(str(avg_price))) * Decimal(str(quantity))
            
        total_value = sum([data.get("quantity", 0) * Decimal(str(data.get("avg_price", Decimal("0.00")))) for symbol, data in account.holdings.items()])
        return PortfolioSummaryResponse(
            holdings=holdings,
            total_value=Decimal(str(total_value)),
            total_pnl=Decimal(str(total_pnl)),
            account=AccountResponse(id=id, balance=balance)
        )
    raise HTTPException(status_code=404,detail="Account not found")
