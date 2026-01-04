from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SubBranch(BaseModel):
    name: str


class Branch(BaseModel):
    name: str
    subbranches: List[str] = []


class MindMapStructure(BaseModel):
    topic: str
    branches: List[Branch]


class MindMapDocument(BaseModel):
    """MongoDB document model for storing mind maps"""
    id: Optional[str] = Field(None, alias="_id")
    student_id: Optional[str] = None
    prompt: str
    topic: str
    svg_content: str
    total_nodes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }