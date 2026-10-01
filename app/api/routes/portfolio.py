from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.exceptions import MissingPriceError
from app.domain.portfolio import Portfolio
from app.repositories.account_repository import AccountRepository
from app.schemas.account_schema import AccountResponse
from app.schemas.portfolio_schema import HoldingSchema, PortfolioSummaryResponse
from app.services.market_data_services import MarketDataService

router = APIRouter(tags=["Holdings"])


@router.get("/accounts/{account_id}/portfolio", response_model=PortfolioSummaryResponse)
async def get_portfolio(
    account_id: int, db: Session = Depends(get_db)
) -> PortfolioSummaryResponse:
    account_repo = AccountRepository(db)
    account = account_repo.get_domain_account(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    market = MarketDataService()
    portfolio = Portfolio(account)

    # Batch fetch all prices concurrently (ADR-011)
    live_prices = await market.get_prices(list(account.holdings.keys()))

    try:
        # Valuation maths lives in the domain layer, not the route.
        total_value = portfolio.total_value(live_prices)
        total_pnl = portfolio.unrealized_pnl(live_prices)
    except MissingPriceError as e:
        # A missing price must not become a fabricated $0.00 valuation.
        raise HTTPException(status_code=503, detail=str(e)) from e

    holdings = [
        HoldingSchema(
            symbol=symbol,
            quantity=position.quantity,
            avg_price=position.avg_price,
            live_price=live_prices.get(symbol),
        )
        for symbol, position in account.holdings.items()
    ]

    return PortfolioSummaryResponse(
        holdings=holdings,
        total_value=total_value,
        total_pnl=total_pnl,
        account=AccountResponse(id=account.id, balance=account.balance),
    )
