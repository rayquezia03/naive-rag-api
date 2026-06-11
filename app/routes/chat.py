from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.retrieval import answer_question

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    return answer_question(request.message)
