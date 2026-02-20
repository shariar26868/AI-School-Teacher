from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ChatRequest(BaseModel):
    assignment_id: str
    student_id: str
    question: str
    interaction_type: str = "ai_response"
    previous_ai_response: Optional[str] = None

class VideoLink(BaseModel):
    title: str
    url: str
    thumbnail: str

class ChatResponse(BaseModel):
    answer: str
    video_links: Optional[List[VideoLink]] = None
    assignment_title: str
    interaction_type: str = "ai_response"

class ChatMessage(BaseModel):
    """Model for storing chat messages in database"""
    student_id: str
    assignment_id: str
    role: str  # "user" or "assistant"
    content: str
    interaction_type: str = "ai_response"  # greeting, ai_response, user_question
    created_at: datetime = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class ChatHistory(BaseModel):
    """Model for retrieving conversation history"""
    assignment_id: str
    student_id: str
    messages: List[dict]
    total_messages: int
    last_updated: datetime