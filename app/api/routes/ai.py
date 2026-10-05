import logging
from functools import lru_cache

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ai_schema import ChatRequest, ChatResponse
from app.services.ai_service import AIChatService

logger = logging.getLogger("ai_audit")
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/ai", tags=["ai"])   


# A single shared instance, created via a dependency rather than at import
# time. Building it at module scope meant a missing GEMINI_API_KEY crashed
# the whole application on startup, taking down /health and /docs along with
# the AI feature that actually needed the key.
@lru_cache(maxsize=1)
def get_ai_service() -> AIChatService:
    return AIChatService()


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    ai_service: AIChatService = Depends(get_ai_service),
) -> ChatResponse:
    reply, actions_taken = await ai_service.chat(
        account_id=request.account_id,
        message=request.message,
        db=db,
    )
    return ChatResponse(reply=reply, actions_taken=actions_taken)
