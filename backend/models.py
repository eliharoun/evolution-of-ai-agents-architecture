"""
Pydantic models for API request/response schemas.
"""
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    stream: bool = True
    stage: int = None  # Optional stage override
    session_id: str = None  # Optional session ID for checkpointing


class ChatResponse(BaseModel):
    """Response model for non-streaming chat."""
    response: str
    thought_process: list
    stage: int
    thread_id: str = None
    struggle_stats: dict = None
