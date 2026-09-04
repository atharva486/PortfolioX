import asyncio
import time
from dotenv import load_dotenv
from app.services.market_data_services import MarketDataService

# Load your Finnhub API Key
load_dotenv()

async def main():
    service = MarketDataService()
    # A list of 10 real stocks to test
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "JPM", "V"]
    
    print(f"📊 Fetching {len(symbols)} symbols from Finnhub...")

    # --- TEST 1: SEQUENTIAL (The old, slow way) ---
    print("\n⏳ Running Sequentially (one by one)...")
    start_seq = time.time()
    for sym in symbols:
        await service.get_price(sym)
    seq_time = time.time() - start_seq
    print(f"🐢 Sequential Time: {seq_time:.2f} seconds")

    # --- TEST 2: CONCURRENT (The new, fast way you built) ---
    print("\n⚡ Running Concurrently (all at once)...")
    start_conc = time.time()
    # This calls your asyncio.gather method!
    await service.get_prices(symbols) 
    conc_time = time.time() - start_conc
    print(f"🚀 Concurrent Time: {conc_time:.2f} seconds")
    
    print(f"\n✅ Concurrency is {seq_time / conc_time:.1f}x faster!")

if __name__ == "__main__":
    asyncio.run(main())