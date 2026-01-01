from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    assignment_id: str
    student_id: str
    question: str

class VideoLink(BaseModel):
    title: str
    url: str
    thumbnail: str

class ChatResponse(BaseModel):
    answer: str
    video_links: Optional[List[VideoLink]] = None
    assignment_title: str