import asyncio
import httpx

# Make sure this matches a real account in your DB that has exactly 1000 balance!
API_URL = "http://127.0.0.1:8000"
ACCOUNT_ID = 1  
ORDER_PAYLOAD = {
    "symbol": "AAPL",
    "asset_type": "Stock",   # Changed to Title Case
    "quantity": 9,
    "order_type": "Market",  # Swapped and Title Case
    "side": "Buy",           # Swapped and Title Case
    "live_price": 100.00,
}
async def fire_order(client, attempt_name):
    print(f"Firing {attempt_name}...")
    response = await client.post(
        f"{API_URL}/accounts/{ACCOUNT_ID}/orders", 
        json=ORDER_PAYLOAD
    )
    print(f"Result {attempt_name}: {response.status_code} - {response.text}")

async def main():
    print("🚀 Starting Race Condition Attack...")
    async with httpx.AsyncClient() as client:
        # Fire both requests at the EXACT same millisecond
        await asyncio.gather(
            fire_order(client, "Request A"),
            fire_order(client, "Request B")
        )

if __name__ == "__main__":
    asyncio.run(main())