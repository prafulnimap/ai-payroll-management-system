import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from app.ai.graph import ask
from app.deps import get_current_user
from app.models import User
from app.schemas import ChatRequest, ChatResponse
from app.services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/query", response_model=ChatResponse)
def chat_query(
    data: ChatRequest, request: Request, user: User = Depends(get_current_user)
):
    request.state.question = data.question

    result = get_cached(user.id, data.question)
    cached = result is not None

    if not cached:
        try:
            result = ask(data.question, user.id)
        except Exception:
            logger.exception("RAG pipeline failed")
            raise HTTPException(
                503, "The AI service is temporarily unavailable. Please try again."
            )
        set_cached(user.id, data.question, result)

    request.state.ai_response = result["answer"]
    return ChatResponse(**result, cached=cached)
