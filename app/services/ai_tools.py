from app.domain.exceptions import AccountNotFoundError, MissingPriceError
from app.services.market_data_services import MarketDataService
from app.repositories.order_repository import OrderRepository
from app.api.routes.portfolio import get_portfolio
from app.api.routes.market import search_symbols,get_live_prices
from app.api.routes.orders import place_order_endpoint
from app.schemas.order_schema import OrderCreate

async def execute_tool(tool_name: str, tool_input: dict, db) -> dict:
    """
    NOTE (security/data-minimization): this sends account balance and holdings
    to a third-party LLM API (Gemini free tier) as part of tool-calling.
    For a production system, this should be scoped down further per-query
    (e.g. only the specific symbol asked about, not the full portfolio),
    and run on an enterprise API tier with a signed data-processing agreement.
    See DECISIONS.md for full reasoning.
    """
    if tool_name == "get_portfolio":
        account = await get_portfolio(tool_input["account_id"],db=db)
        if account is None:
            raise AccountNotFoundError(f"Account with ID {tool_input['account_id']} not found.")
        return account.model_dump(mode="json")

    if tool_name == "get_live_price":
        market = MarketDataService()
        price = await market.get_price(tool_input["symbol"])
        if price is None:
            raise ValueError(f"Live price for symbol {tool_input['symbol']} not found.")
        return {"symbol": tool_input["symbol"], "price": str(price)}

    if tool_name == "place_order":
        market = MarketDataService()
        live_price = await market.get_price(tool_input["symbol"])
        if live_price is None:
            raise MissingPriceError(f"Live price for symbol {tool_input['symbol']} not found.")
        order_repo = OrderRepository(db)
        result = order_repo.place_order(
            live_price=live_price,
            symbol=tool_input["symbol"],
            account_id=tool_input["account_id"],
            order_side=tool_input["order_side"],
            limit_price=None,  
            order_type=tool_input["order_type"],
            quantity=tool_input["quantity"],
        )
        order = OrderCreate(symbol=tool_input["symbol"],quantity=tool_input["quantity"],order_type=tool_input["order_type"],side=tool_input["order_side"],limit_price=None)
        result = await place_order_endpoint(tool_input["account_id"],order_in=order,db=db)
        return result if result is not None else {"status": "FAILED", "reason": "Order could not be placed."}
    raise ValueError(f"Unknown tool name: {tool_name}")