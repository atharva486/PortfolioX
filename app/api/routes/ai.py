import os
import logging
from google import genai
from google.genai import types
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.ai_tools import execute_tool

logger = logging.getLogger("ai_audit")
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/ai", tags=["ai"])
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are a helpful assistant for PortfolioX, a trading portfolio app.
You can look up a user's portfolio using the get_portfolio tool. Only use account_id
values the user gives you. If asked anything unrelated to portfolios, politely say
you can only help with portfolio questions right now."""

get_portfolio_fn = types.FunctionDeclaration(
    name="get_portfolio",
    description="Get current holdings and cash balance for a trading account.",
    parameters={
        "type": "object",
        "properties": {"account_id": {"type": "integer"}},
        "required": ["account_id"],
    },
)

get_live_price_fn = types.FunctionDeclaration(
    name="get_live_price",
    description="Get the current live market price for a stock symbol.",
    parameters={
        "type": "object",
        "properties": {"symbol": {"type": "string"}},
        "required": ["symbol"],
    },
)

TOOLS = types.Tool(function_declarations=[get_portfolio_fn, get_live_price_fn])


class ChatRequest(BaseModel):
    account_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
    actions_taken: list[str] = []


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest, db: Session = Depends(get_db)):
    actions_taken = []
    contents = [
        types.Content(role="user", parts=[types.Part(text=f"(account_id={request.account_id}) {request.message}")])
    ]
    config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, tools=[TOOLS])

    while True:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=config,
        )
        candidate = response.candidates[0]
        function_calls = [p.function_call for p in candidate.content.parts if p.function_call]

        if not function_calls:
            final_text = "".join(p.text for p in candidate.content.parts if p.text)
            return ChatResponse(reply=final_text, actions_taken=actions_taken)

        contents.append(candidate.content)
        function_response_parts = []
        for fc in function_calls:
            actions_taken.append(f"{fc.name}({dict(fc.args)})")
            logger.info(f"AI_TOOL_CALL account_id={request.account_id} tool={fc.name} args={dict(fc.args)}")
            result = await execute_tool(fc.name, dict(fc.args), db)
            function_response_parts.append(
                types.Part.from_function_response(name=fc.name, response={"result": result})
            )
        contents.append(types.Content(role="user", parts=function_response_parts))