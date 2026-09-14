import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ai_schema import ChatRequest, ChatResponse
from app.services.ai_service import AIChatService

logger = logging.getLogger("ai_audit")
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/ai", tags=["ai"])

ai_service = AIChatService()


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest, db: Session = Depends(get_db)):
    reply, actions_taken = await ai_service.chat(
        account_id=request.account_id,
        message=request.message,
        db=db,
    )
    return ChatResponse(reply=reply, actions_taken=actions_taken)