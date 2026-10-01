from app.api.routes.orders import place_order_endpoint
from app.api.routes.portfolio import get_portfolio
from app.domain.exceptions import AccountNotFoundError
from app.schemas.order_schema import OrderCreate
from app.services.market_data_services import MarketDataService


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
        account = await get_portfolio(tool_input["account_id"], db=db)
        if account is None:
            raise AccountNotFoundError(
                f"Account with ID {tool_input['account_id']} not found."
            )
        return account.model_dump(mode="json")

    if tool_name == "get_live_price":
        market = MarketDataService()
        price = await market.get_price(tool_input["symbol"])
        if price is None:
            raise ValueError(f"Live price for symbol {tool_input['symbol']} not found.")
        return {"symbol": tool_input["symbol"], "price": str(price)}

    if tool_name == "place_order":
        # NOTE: this previously called order_repo.place_order() and then
        # called the place_order_endpoint() route, discarding the first
        # result. Every AI-placed order was executed TWICE. The tool now
        # delegates to the route exactly once.
        order = OrderCreate(
            symbol=tool_input["symbol"],
            quantity=tool_input["quantity"],
            order_type=tool_input["order_type"],
            side=tool_input["order_side"],
            limit_price=tool_input.get("limit_price"),
        )
        result = await place_order_endpoint(
            tool_input["account_id"], order_in=order, db=db
        )
        return result.model_dump(mode="json")

    raise ValueError(f"Unknown tool name: {tool_name}")
