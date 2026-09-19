import os
import logging

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
        properties={"account_id": types.Schema(type=types.Type.INTEGER)},
        required=["account_id"],
    ),
)

get_live_price_fn = types.FunctionDeclaration(
    name="get_live_price",
    description="Get the current live market price for a stock symbol.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={"symbol": types.Schema(type=types.Type.STRING, description="Stock symbol to look up")},
        required=["symbol"],
    ),
)

TOOLS = types.Tool(function_declarations=[get_portfolio_fn, get_live_price_fn])


class AIChatService:
    """Encapsulates the Gemini chat loop and tool-calling orchestration."""

    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    async def chat(self, account_id: int, message: str, db: Session) -> tuple[str, list[str]]:
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
            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents,
                config=config,
            )
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
                final_text = "".join(
                    p.text for p in candidate.content.parts if p.text
                )
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
                function_response_parts.append(
                    types.Part.from_function_response(
                        name=fc.name, response={"result": result}
                    )
                )
            contents.append(
                types.Content(role="user", parts=function_response_parts)
            )
