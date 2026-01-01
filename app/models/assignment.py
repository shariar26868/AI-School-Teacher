from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AssignmentPage(BaseModel):
    page_number: int
    content: str
    extraction_method: str

class AssignmentCreate(BaseModel):
    title: str
    subject: Optional[str] = None
    teacher_id: str

class AssignmentResponse(BaseModel):
    id: str
    title: str
    subject: Optional[str]
    teacher_id: str
    file_url: str
    total_pages: int
    upload_date: datetime
    status: str

class AssignmentList(BaseModel):
    assignments: List[AssignmentResponse]
    total: int

# NEW: For handling failed uploads in bulk
class FailedUpload(BaseModel):
    file_name: str
    error: str

# NEW: For bulk upload response
class BulkUploadResponse(BaseModel):
    successful: List[AssignmentResponse]
    failed: List[FailedUpload]
    total_processed: int
    total_successful: int
    total_failed: int