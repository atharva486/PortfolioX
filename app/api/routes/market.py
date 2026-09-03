from fastapi import APIRouter, Depends, Query
from app.schemas.market_schema import AssetSearchRequest
from app.services.market_data_services import MarketDataService

router = APIRouter(prefix="/api/market", tags=["Market Data"])

def get_market_service():
    return MarketDataService()

@router.get("/search", response_model=list[AssetSearchRequest])
async def search_symbols(
    # This forces the URL to be: /api/market/search?query=AAPL
    query: str = Query(..., min_length=1, description="Type a company name or ticker symbol"),
    service: MarketDataService = Depends(get_market_service)
):
    return await service.search_assets(query)