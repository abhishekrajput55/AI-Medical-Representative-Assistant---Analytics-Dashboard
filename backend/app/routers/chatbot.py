"""
Chatbot endpoints: ask a question, view your own chat history,
and (for Product Managers/Admins) rebuild the AI's knowledge base.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessageOut, ReindexResponse
from app.ai.rag_service import ask_medical_assistant
from app.ai.vectorstore import reindex_all_products

router = APIRouter(prefix="/api/chatbot", tags=["AI Chatbot"])


@router.post("/ask", response_model=ChatResponse)
def ask(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = ask_medical_assistant(payload.question)

    # Save the exchange to history so the user can scroll back later.
    chat_record = ChatMessage(
        user_id=current_user.id,
        question=payload.question,
        answer=result["answer"],
        sources=result["sources"],
    )
    db.add(chat_record)
    db.commit()

    return ChatResponse(answer=result["answer"], sources=result["sources"])


@router.get("/history", response_model=list[ChatMessageOut])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the current user's own chat history, most recent first."""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(100)
        .all()
    )


@router.post(
    "/reindex", response_model=ReindexResponse,
    dependencies=[Depends(require_role(UserRole.PRODUCT_MANAGER, UserRole.ADMIN))],
)
def reindex(db: Session = Depends(get_db)):
    """
    Rebuilds the AI's knowledge base from every product currently in
    the database. Run this after bulk-editing products, or any time
    the AI's answers seem out of date.
    """
    products = db.query(Product).all()
    count = reindex_all_products(products)
    return ReindexResponse(
        indexed_count=count,
        message=f"Successfully indexed {count} products into the AI knowledge base.",
    )
