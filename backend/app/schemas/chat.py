import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    question: str
    answer: str
    sources: list[str] | None
    created_at: datetime

    class Config:
        from_attributes = True


class ReindexResponse(BaseModel):
    indexed_count: int
    message: str
