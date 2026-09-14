from pydantic import BaseModel


class ChatRequest(BaseModel):
    account_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
    actions_taken: list[str] = []
