# from pydantic import BaseModel, Field
# from typing import List, Optional
# from datetime import datetime


# class SubBranch(BaseModel):
#     name: str


# class Branch(BaseModel):
#     name: str
#     subbranches: List[str] = []


# class MindMapStructure(BaseModel):
#     topic: str
#     branches: List[Branch]


# class MindMapDocument(BaseModel):
#     """MongoDB document model for storing mind maps"""
#     id: Optional[str] = Field(None, alias="_id")
#     student_id: Optional[str] = None
#     prompt: str
#     topic: str
#     svg_content: str
#     total_nodes: int
#     created_at: datetime = Field(default_factory=datetime.utcnow)
    
#     class Config:
#         populate_by_name = True
#         json_encoders = {
#             datetime: lambda v: v.isoformat()
#         }






from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MindMapRequest(BaseModel):
    prompt: str
    student_id: Optional[str] = None
    format: str = "png"


class MindMapResponse(BaseModel):
    image_url: str
    image_base64: Optional[str] = None
    topic: str
    total_nodes: int
    format: str
    theme: Optional[str] = None
    mongo_id: Optional[str] = None


class MindMapDocument(BaseModel):
    """MongoDB document model for storing mind maps"""
    id: Optional[str] = Field(None, alias="_id")
    student_id: Optional[str] = None
    prompt: str
    topic: str
    image_base64: str
    total_nodes: int
    theme: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MindMapListItem(BaseModel):
    """Lightweight model for listing mindmaps (no image_base64)"""
    id: Optional[str] = Field(None, alias="_id")
    student_id: Optional[str] = None
    prompt: str
    topic: str
    total_nodes: int
    theme: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }