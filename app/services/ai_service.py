import asyncio
import logging
import os
from decimal import Decimal
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.services.ai_tools import execute_tool

logger = logging.getLogger("ai_audit")

SYSTEM_PROMPT = """You are a helpful assistant for PortfolioX, a trading portfolio app.
You can look up a user's portfolio using the get_portfolio tool. Only use account_id
values the user gives you. If asked anything unrelated to portfolios, politely say
you can only help with portfolio questions right now."""

get_portfolio_fn = types.FunctionDeclaration(
    name="get_portfolio",
    description="Get current holdings and cash balance for a trading account.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "account_id": types.Schema(type=types.Type.INTEGER),
        },
        required=["account_id"],
    ),
)

get_live_price_fn = types.FunctionDeclaration(
    name="get_live_price",
    description="Get the current live market price for a stock symbol.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "symbol": types.Schema(
                type=types.Type.STRING, description="Stock symbol to look up"
            )
        },
        required=["symbol"],
    ),
)

place_order_fn = types.FunctionDeclaration(
    name="place_order",
    description="Place a buy or sell order for a stock symbol.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "account_id": types.Schema(
                type=types.Type.INTEGER,
                description="The account ID to place the order for.",
            ),
            "symbol": types.Schema(
                type=types.Type.STRING, description="The stock symbol to trade."
            ),
            "order_type": types.Schema(
                type=types.Type.STRING,
                enum=["0", "1"],
                description="Type of order: '0' for MARKET, '1' for LIMIT.",
            ),
            "quantity": types.Schema(
                type=types.Type.NUMBER,
                description="The number of shares to buy or sell.",
            ),
            "order_side": types.Schema(
                type=types.Type.STRING,
                enum=["0", "1"],
                description="Side of order: '0' for BUY, '1' for SELL.",
            ),
        },
        required=["account_id", "symbol", "order_type", "quantity", "order_side"],
    ),
)

TOOLS = types.Tool(
    function_declarations=[get_portfolio_fn, get_live_price_fn, place_order_fn]
)


class AIChatService:
    """Encapsulates the Gemini chat loop and tool-calling orchestration."""

    MODEL_FALLBACKS = ["gemini-3.8-flash"]

    def __init__(self) -> None:
        # The client is built LAZILY, on first use, not here.
        #
        # Constructing it in __init__ meant `app.main` could not even be
        # imported without GEMINI_API_KEY set, because the router module
        # instantiated this class at import time. That broke the Docker
        # healthcheck, /docs, and every non-AI endpoint in an environment
        # without a key. A missing optional integration should degrade one
        # feature, not take down the whole process.
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY is not configured. The AI endpoints are "
                    "unavailable; the rest of the API is unaffected."
                )
            self._client = genai.Client(api_key=api_key)
        return self._client

    def convert_decimals(self, obj: Any) -> Any:
        """Recursively converts any Decimal values to float (or str) so JSON serialization works."""
        if isinstance(obj, dict):
            return {k: self.convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_decimals(i) for i in obj]
        elif isinstance(obj, Decimal):
            # Use float(obj) for numbers, or str(obj) if you want exact string precision
            return float(obj)
        return obj

    async def chat(
        self, account_id: int, message: str, db: Session
    ) -> tuple[str, list[str]]:
        """
        Run a multi-turn chat with Gemini, resolving any tool calls along the way.

        Returns:
            A tuple of (reply_text, actions_taken).
        """
        actions_taken: list[str] = []
        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=f"(account_id={account_id}) {message}")],
            )
        ]
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT, tools=[TOOLS]
        )

        while True:
            response = None
            last_error = None
            for model_name in self.MODEL_FALLBACKS:
                for attempt in range(5):  # retry up to 5 times
                    try:
                        response = await self.client.aio.models.generate_content(
                            model=model_name,
                            contents=contents,
                            config=config,
                        )
                        break  # success
                    except Exception as e:
                        last_error = e
                        wait = min(
                            2**attempt, 30
                        )  # backoff: 1, 2, 4, 8, 16s (capped at 30)
                        logger.warning(
                            f"Model {model_name} attempt {attempt + 1} failed — retrying in {wait}s: {e}"
                        )
                        await asyncio.sleep(wait)
                if response:
                    break
            if not response:
                raise RuntimeError(f"All models failed. Last error: {last_error}")

            if not response.candidates or not response.candidates[0].content:
                raise RuntimeError("No candidates returned from Gemini API.")
            candidate = response.candidates[0]

            if not candidate.content:
                raise RuntimeError("No content parts returned from Gemini API.")

            if not candidate.content.parts:
                raise RuntimeError("No content parts returned from Gemini API.")
            function_calls = [
                p.function_call for p in candidate.content.parts if p.function_call
            ]

            if not function_calls:
                final_text = "".join(p.text for p in candidate.content.parts if p.text)
                return final_text, actions_taken

            contents.append(candidate.content)
            function_response_parts = []
            for fc in function_calls:
                if not fc.name or not fc.args:
                    raise RuntimeError(
                        "Function call missing name or args in Gemini API response."
                    )
                actions_taken.append(f"{fc.name}({dict(fc.args)})")
                logger.info(
                    f"AI_TOOL_CALL account_id={account_id} tool={fc.name} args={dict(fc.args)}"
                )
                result = await execute_tool(fc.name, dict(fc.args), db)
                clean_result = self.convert_decimals(result)
                function_response_parts.append(
                    types.Part.from_function_response(
                        name=fc.name, response={"result": clean_result}
                    )
                )
            contents.append(types.Content(role="user", parts=function_response_parts))
