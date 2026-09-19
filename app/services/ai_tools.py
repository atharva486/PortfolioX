from app.domain.exceptions import AccountNotFoundError
from app.repositories.account_repository import AccountRepository
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
        account_repo = AccountRepository(db)
        account = account_repo.get_domain_account(tool_input["account_id"])
        if account is None:
            raise AccountNotFoundError(f"Account with ID {tool_input['account_id']} not found.")

        holdings_summary = [
            {
                "symbol": sym,
                "quantity": str(h["quantity"]),
                "avg_price": str(h["avg_price"]),
            }
            for sym, h in account.holdings.items()
        ]
        return {
            "cash_balance": str(account.balance),
            "holdings": holdings_summary,
        }

    if tool_name == "get_live_price":
        market = MarketDataService()
        price = await market.get_price(tool_input["symbol"])
        if price is None:
            raise ValueError(f"Live price for symbol {tool_input['symbol']} not found.")
        return {"symbol": tool_input["symbol"], "price": str(price)}

    raise ValueError(f"Unknown tool name: {tool_name}")