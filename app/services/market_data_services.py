from app.domain.asset import AssetType
import httpx
import asyncio
import os
from decimal import Decimal
import logging
from app.schemas.market_schema import AssetSearchRequest
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class MarketDataService:
    def __init__(self):
        self.api_key = os.getenv("FINHUB_API_KEY")
        self.base_url = "https://finnhub.io/api/v1"

    async def get_price(self, symbol: str) -> Decimal | None:
        """Fetches a single live price from Finnhub."""
        if not self.api_key:
            logger.error("FINNHUB_API_KEY is not set.")
            return None

        # Fallback for bonds or test assets that Finnhub doesn't support
        if symbol.lower() in ["bnd", "us-t"]:
            return Decimal("100.00")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/quote",
                    params={"symbol": symbol, "token": self.api_key},
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Finnhub returns 'c' for current price
                current_price = data.get("c")
                if current_price and current_price > 0:
                    return Decimal(str(current_price))
                return None
            except Exception as e:
                logger.error(f"Finnhub API failed for {symbol}: {e}")
                return None

    async def get_prices(self, symbols: list[str]) -> dict[str, Decimal]:
        """Fetches multiple prices concurrently using asyncio.gather."""
        # Remove duplicates to avoid redundant API calls
        unique_symbols = list(set(symbols))
        
        tasks = [self.get_price(sym) for sym in unique_symbols]
        results = await asyncio.gather(*tasks)
        
        # Zip symbols back to results, dropping failures
        return {
            sym: price for sym, price in zip(unique_symbols, results) if price is not None
        }
    
    def map_finnhub_type_to_domain(self,finnhub_type: str) -> AssetType:
        if "bond" in finnhub_type.lower():
            return AssetType.BOND
        return AssetType.STOCK

    async def search_assets(self, query: str) -> list[AssetSearchRequest]:
        """Searches Finnhub for matching company names or tickers."""
        print(f"🕵️ DEBUG: API Key Loaded? -> {self.api_key}")
        if not self.api_key:
            return []
        

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={"q": query, "token": self.api_key},
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()
                print(f"🕵️ DEBUG: Finnhub Raw Data -> {data}")
                
                results = data.get("result", [])
                
                # Only keep valid equities/ETFs/Bonds and map them to our Domain Enum
                formatted_results = []
                for item in results:
                    raw_type = item.get("type", "")
                    if raw_type in ["Common Stock", "ETP", "ETF"] or "bond" in raw_type.lower():
                        formatted_results.append(
                            AssetSearchRequest(
                                symbol=item["symbol"],
                                name=item.get("description", ""),
                                asset_type=self.map_finnhub_type_to_domain(raw_type),
                                sector="Technology" if raw_type == "Common Stock" else None, 
                                coupon_rate=None
                            )
                        )
                
                return formatted_results
            except Exception as e:
                import traceback
                print(f"🚨 BOOM: Search failed for '{query}'")
                print(f"🚨 Error Details: {repr(e)}")
                traceback.print_exc()
                
                logger.error(f"Search failed for '{query}': {e}")
                return []