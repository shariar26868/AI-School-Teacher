# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# from typing import List
# from app.services.file_processor import process_uploaded_file
# from app.services.s3_service import upload_to_s3
# from app.services.ocr_service import extract_text_from_file
# from app.services.db_service import save_assignment, get_all_assignments
# from app.models.assignment import AssignmentResponse, AssignmentList
# import uuid
# from datetime import datetime
# import asyncio

# router = APIRouter()

# @router.post("/assignments/upload", response_model=AssignmentResponse)
# async def upload_assignment(
#     file: UploadFile = File(...),
#     title: str = Form(...),
#     subject: str = Form(None),
#     teacher_id: str = Form(...)
# ):
#     """
#     Upload an assignment (PDF, image, DOCX, etc.)
#     """
#     try:
#         # Generate unique ID
#         assignment_id = str(uuid.uuid4())
        
#         # Save file temporarily
#         temp_path = await process_uploaded_file(file, assignment_id)
        
#         # Upload to S3
#         s3_url = await upload_to_s3(temp_path, assignment_id, file.filename)
        
#         # Extract text using OCR
#         pages_data = await extract_text_from_file(temp_path)
        
#         # Save to MongoDB
#         assignment_data = {
#             "id": assignment_id,
#             "title": title,
#             "subject": subject,
#             "teacher_id": teacher_id,
#             "file_url": s3_url,
#             "file_name": file.filename,
#             "file_type": file.content_type,
#             "pages": pages_data,
#             "total_pages": len(pages_data),
#             "full_text": " ".join([page["content"] for page in pages_data]),
#             "upload_date": datetime.utcnow(),
#             "status": "processed"
#         }
        
#         await save_assignment(assignment_data)
        
#         return AssignmentResponse(
#             id=assignment_id,
#             title=title,
#             subject=subject,
#             teacher_id=teacher_id,
#             file_url=s3_url,
#             total_pages=len(pages_data),
#             upload_date=assignment_data["upload_date"],
#             status="processed"
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# @router.post("/assignments/upload-multiple", response_model=List[AssignmentResponse])
# async def upload_multiple_assignments(
#     files: List[UploadFile] = File(...),
#     titles: str = Form(...),  # Comma-separated titles
#     subjects: str = Form(None),  # Comma-separated subjects
#     teacher_id: str = Form(...)
# ):
#     """
#     Upload multiple assignments at once
#     titles and subjects should be comma-separated strings matching the number of files
#     """
#     try:
#         # Parse titles and subjects
#         title_list = [t.strip() for t in titles.split(',')]
#         subject_list = [s.strip() for s in subjects.split(',')] if subjects else [None] * len(files)
        
#         # Validate input
#         if len(title_list) != len(files):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Number of titles ({len(title_list)}) must match number of files ({len(files)})"
#             )
        
#         if subjects and len(subject_list) != len(files):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Number of subjects ({len(subject_list)}) must match number of files ({len(files)})"
#             )
        
#         # Process each file
#         async def process_single_file(file: UploadFile, title: str, subject: str):
#             try:
#                 assignment_id = str(uuid.uuid4())
#                 temp_path = await process_uploaded_file(file, assignment_id)
#                 s3_url = await upload_to_s3(temp_path, assignment_id, file.filename)
#                 pages_data = await extract_text_from_file(temp_path)
                
#                 assignment_data = {
#                     "id": assignment_id,
#                     "title": title,
#                     "subject": subject,
#                     "teacher_id": teacher_id,
#                     "file_url": s3_url,
#                     "file_name": file.filename,
#                     "file_type": file.content_type,
#                     "pages": pages_data,
#                     "total_pages": len(pages_data),
#                     "full_text": " ".join([page["content"] for page in pages_data]),
#                     "upload_date": datetime.utcnow(),
#                     "status": "processed"
#                 }
                
#                 await save_assignment(assignment_data)
                
#                 return AssignmentResponse(
#                     id=assignment_id,
#                     title=title,
#                     subject=subject,
#                     teacher_id=teacher_id,
#                     file_url=s3_url,
#                     total_pages=len(pages_data),
#                     upload_date=assignment_data["upload_date"],
#                     status="processed"
#                 )
#             except Exception as e:
#                 # Return error info for this specific file
#                 return {
#                     "error": True,
#                     "file_name": file.filename,
#                     "message": str(e)
#                 }
        
#         # Process all files concurrently
#         tasks = [
#             process_single_file(file, title, subject)
#             for file, title, subject in zip(files, title_list, subject_list)
#         ]
#         results = await asyncio.gather(*tasks, return_exceptions=False)
        
#         # Separate successful uploads from failures
#         successful = [r for r in results if not isinstance(r, dict) or not r.get("error")]
#         failed = [r for r in results if isinstance(r, dict) and r.get("error")]
        
#         if failed:
#             # If some failed, include error info in response
#             raise HTTPException(
#                 status_code=207,  # Multi-Status
#                 detail={
#                     "message": f"Processed {len(successful)} files successfully, {len(failed)} failed",
#                     "successful": successful,
#                     "failed": failed
#                 }
#             )
        
#         return successful
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")


# @router.get("/assignments", response_model=AssignmentList)
# async def list_assignments(teacher_id: str = None):
#     """
#     Get all uploaded assignments
#     """
#     try:
#         assignments = await get_all_assignments(teacher_id)
#         return AssignmentList(
#             assignments=assignments,
#             total=len(assignments)
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
# async def get_assignment(assignment_id: str):
#     """
#     Get specific assignment details
#     """
#     try:
#         from app.services.db_service import get_assignment_by_id
#         assignment = await get_assignment_by_id(assignment_id)
#         if not assignment:
#             raise HTTPException(status_code=404, detail="Assignment not found")
#         return assignment
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))






# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# from typing import List, Optional
# from app.services.file_processor import process_uploaded_file, cleanup_temp_files
# from app.services.s3_service import upload_to_s3
# from app.services.ocr_service import extract_text_from_file
# from app.services.db_service import save_assignment, get_all_assignments
# from app.models.assignment import (
#     AssignmentResponse, 
#     AssignmentList,           # ✅ এটা add করা হয়েছে
#     BulkUploadResponse, 
#     FailedUpload
# )
# import uuid
# from datetime import datetime
# import asyncio

# router = APIRouter()

# @router.post("/assignments/upload", response_model=AssignmentResponse)
# async def upload_assignment(
#     file: UploadFile = File(...),
#     title: str = Form(...),
#     subject: str = Form(None),
#     teacher_id: str = Form(...)
# ):
#     """
#     Upload a single assignment (PDF, image, DOCX, etc.)
#     """
#     try:
#         assignment_id = str(uuid.uuid4())
#         temp_path = await process_uploaded_file(file, assignment_id)
#         s3_url = await upload_to_s3(temp_path, assignment_id, file.filename)
#         pages_data = await extract_text_from_file(temp_path)
        
#         assignment_data = {
#             "id": assignment_id,
#             "title": title,
#             "subject": subject,
#             "teacher_id": teacher_id,
#             "file_url": s3_url,
#             "file_name": file.filename,
#             "file_type": file.content_type,
#             "pages": pages_data,
#             "total_pages": len(pages_data),
#             "full_text": " ".join([page["content"] for page in pages_data]),
#             "upload_date": datetime.utcnow(),
#             "status": "processed"
#         }
        
#         await save_assignment(assignment_data)
        
#         from app.services.file_processor import cleanup_temp_file
#         cleanup_temp_file(temp_path)
        
#         return AssignmentResponse(
#             id=assignment_id,
#             title=title,
#             subject=subject,
#             teacher_id=teacher_id,
#             file_url=s3_url,
#             total_pages=len(pages_data),
#             upload_date=assignment_data["upload_date"],
#             status="processed"
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# @router.post("/assignments/upload-multiple", response_model=BulkUploadResponse)
# async def upload_multiple_assignments(
#     files: List[UploadFile] = File(..., description="Upload multiple files"),
#     titles: List[str] = Form(..., description="Titles for each file (in same order)"),
#     subjects: List[Optional[str]] = Form(None, description="Subjects for each file (optional, in same order)"),
#     teacher_id: str = Form(..., description="Teacher ID for all assignments")
# ):
#     """
#     Upload multiple assignments at once.
    
#     Example:
#     - files: [file1.pdf, file2.pdf, file3.pdf]
#     - titles: ["History Assignment", "Math Homework", "English Essay"]
#     - subjects: ["History", "Mathematics", "English"]
#     - teacher_id: "teacher123"
    
#     Note: Number of titles must match number of files.
#     Subjects is optional but if provided, must match number of files.
#     """
#     try:
#         # Validate input
#         if len(titles) != len(files):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Number of titles ({len(titles)}) must match number of files ({len(files)})"
#             )
        
#         # Handle subjects - if None or empty, create list of None
#         if not subjects or all(s is None or s == "" for s in subjects):
#             subjects = [None] * len(files)
#         elif len(subjects) != len(files):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Number of subjects ({len(subjects)}) must match number of files ({len(files)})"
#             )
        
#         successful = []
#         failed = []
#         temp_files = []
        
#         # Process each file
#         async def process_single_file(file: UploadFile, title: str, subject: Optional[str], index: int):
#             temp_path = None
#             try:
#                 assignment_id = str(uuid.uuid4())
#                 temp_path = await process_uploaded_file(file, assignment_id)
#                 temp_files.append(temp_path)
                
#                 s3_url = await upload_to_s3(temp_path, assignment_id, file.filename)
#                 pages_data = await extract_text_from_file(temp_path)
                
#                 assignment_data = {
#                     "id": assignment_id,
#                     "title": title,
#                     "subject": subject,
#                     "teacher_id": teacher_id,
#                     "file_url": s3_url,
#                     "file_name": file.filename,
#                     "file_type": file.content_type,
#                     "pages": pages_data,
#                     "total_pages": len(pages_data),
#                     "full_text": " ".join([page["content"] for page in pages_data]),
#                     "upload_date": datetime.utcnow(),
#                     "status": "processed"
#                 }
                
#                 await save_assignment(assignment_data)
                
#                 return {
#                     "success": True,
#                     "data": AssignmentResponse(
#                         id=assignment_id,
#                         title=title,
#                         subject=subject,
#                         teacher_id=teacher_id,
#                         file_url=s3_url,
#                         total_pages=len(pages_data),
#                         upload_date=assignment_data["upload_date"],
#                         status="processed"
#                     )
#                 }
#             except Exception as e:
#                 return {
#                     "success": False,
#                     "error": FailedUpload(
#                         file_name=file.filename,
#                         error=str(e)
#                     )
#                 }
        
#         # Process all files concurrently
#         tasks = [
#             process_single_file(file, title, subject, idx)
#             for idx, (file, title, subject) in enumerate(zip(files, titles, subjects))
#         ]
#         results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         # Separate successful uploads from failures
#         for result in results:
#             if isinstance(result, Exception):
#                 failed.append(FailedUpload(file_name="unknown", error=str(result)))
#             elif result["success"]:
#                 successful.append(result["data"])
#             else:
#                 failed.append(result["error"])
        
#         # Cleanup temp files
#         await cleanup_temp_files(temp_files)
        
#         return BulkUploadResponse(
#             successful=successful,
#             failed=failed,
#             total_processed=len(files),
#             total_successful=len(successful),
#             total_failed=len(failed)
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")


# @router.get("/assignments", response_model=AssignmentList)
# async def list_assignments(teacher_id: str = None):
#     """
#     Get all uploaded assignments
#     """
#     try:
#         assignments = await get_all_assignments(teacher_id)
#         return AssignmentList(
#             assignments=assignments,
#             total=len(assignments)
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
# async def get_assignment(assignment_id: str):
#     """
#     Get specific assignment details
#     """
#     try:
#         from app.services.db_service import get_assignment_by_id
#         assignment = await get_assignment_by_id(assignment_id)
#         if not assignment:
#             raise HTTPException(status_code=404, detail="Assignment not found")
#         return assignment
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))




# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# from typing import List, Optional
# from app.services.file_processor import process_uploaded_file, cleanup_temp_files
# from app.services.s3_service import upload_to_s3
# from app.services.ocr_service import extract_text_from_file
# from app.services.db_service import save_assignment, get_all_assignments
# from app.models.assignment import (
#     AssignmentResponse, 
#     AssignmentList,
#     BulkUploadResponse, 
#     FailedUpload
# )
# import uuid
# from datetime import datetime
# import asyncio

# router = APIRouter()

# @router.post("/assignments/upload", response_model=AssignmentResponse)
# async def upload_assignment(
#     file: UploadFile = File(...),
#     title: str = Form(...),
#     subject: str = Form(None),
#     teacher_id: str = Form(...)
# ):
#     """
#     Upload a single assignment (PDF, image, DOCX, etc.)
#     """
#     try:
#         assignment_id = str(uuid.uuid4())
#         temp_path = await process_uploaded_file(file, assignment_id)
#         s3_url = await upload_to_s3(temp_path, assignment_id, file.filename)
#         pages_data = await extract_text_from_file(temp_path)
        
#         assignment_data = {
#             "id": assignment_id,
#             "title": title,
#             "subject": subject,
#             "teacher_id": teacher_id,
#             "file_url": s3_url,
#             "file_name": file.filename,
#             "file_type": file.content_type,
#             "pages": pages_data,
#             "total_pages": len(pages_data),
#             "full_text": " ".join([page["content"] for page in pages_data]),
#             "upload_date": datetime.utcnow(),
#             "status": "processed"
#         }
        
#         await save_assignment(assignment_data)
        
#         from app.services.file_processor import cleanup_temp_file
#         cleanup_temp_file(temp_path)
        
#         return AssignmentResponse(
#             id=assignment_id,
#             title=title,
#             subject=subject,
#             teacher_id=teacher_id,
#             file_url=s3_url,
#             total_pages=len(pages_data),
#             upload_date=assignment_data["upload_date"],
#             status="processed"
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# @router.post("/assignments/upload-multiple", response_model=BulkUploadResponse)
# async def upload_multiple_assignments(
#     files: List[UploadFile] = File(..., description="Upload multiple files"),
#     titles: List[str] = Form(..., description="Titles for each file (in same order)"),
#     teacher_ids: List[str] = Form(..., description="Teacher IDs for each file (in same order)"),
#     subjects: List[Optional[str]] = Form(None, description="Subjects for each file (optional, in same order)")
# ):
#     """
#     Upload multiple assignments at once.
    
#     Example:
#     - files: [file1.pdf, file2.pdf, file3.pdf]
#     - titles: ["History Assignment", "Math Homework", "English Essay"]
#     - teacher_ids: ["teacher123", "teacher456", "teacher123"]
#     - subjects: ["History", "Mathematics", "English"]
    
#     Note: Number of titles and teacher_ids must match number of files.
#     Subjects is optional but if provided, must match number of files.
#     """
#     try:
#         # Validate input
#         if len(titles) != len(files):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Number of titles ({len(titles)}) must match number of files ({len(files)})"
#             )
        
#         if len(teacher_ids) != len(files):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Number of teacher_ids ({len(teacher_ids)}) must match number of files ({len(files)})"
#             )
        
#         # Handle subjects - if None or empty, create list of None
#         if not subjects or all(s is None or s == "" for s in subjects):
#             subjects = [None] * len(files)
#         elif len(subjects) != len(files):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Number of subjects ({len(subjects)}) must match number of files ({len(files)})"
#             )
        
#         successful = []
#         failed = []
#         temp_files = []
        
#         # Process each file
#         async def process_single_file(file: UploadFile, title: str, teacher_id: str, subject: Optional[str], index: int):
#             temp_path = None
#             try:
#                 assignment_id = str(uuid.uuid4())
#                 temp_path = await process_uploaded_file(file, assignment_id)
#                 temp_files.append(temp_path)
                
#                 s3_url = await upload_to_s3(temp_path, assignment_id, file.filename)
#                 pages_data = await extract_text_from_file(temp_path)
                
#                 assignment_data = {
#                     "id": assignment_id,
#                     "title": title,
#                     "subject": subject,
#                     "teacher_id": teacher_id,
#                     "file_url": s3_url,
#                     "file_name": file.filename,
#                     "file_type": file.content_type,
#                     "pages": pages_data,
#                     "total_pages": len(pages_data),
#                     "full_text": " ".join([page["content"] for page in pages_data]),
#                     "upload_date": datetime.utcnow(),
#                     "status": "processed"
#                 }
                
#                 await save_assignment(assignment_data)
                
#                 return {
#                     "success": True,
#                     "data": AssignmentResponse(
#                         id=assignment_id,
#                         title=title,
#                         subject=subject,
#                         teacher_id=teacher_id,
#                         file_url=s3_url,
#                         total_pages=len(pages_data),
#                         upload_date=assignment_data["upload_date"],
#                         status="processed"
#                     )
#                 }
#             except Exception as e:
#                 return {
#                     "success": False,
#                     "error": FailedUpload(
#                         file_name=file.filename,
#                         error=str(e)
#                     )
#                 }
        
#         # Process all files concurrently
#         tasks = [
#             process_single_file(file, title, teacher_id, subject, idx)
#             for idx, (file, title, teacher_id, subject) in enumerate(zip(files, titles, teacher_ids, subjects))
#         ]
#         results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         # Separate successful uploads from failures
#         for result in results:
#             if isinstance(result, Exception):
#                 failed.append(FailedUpload(file_name="unknown", error=str(result)))
#             elif result["success"]:
#                 successful.append(result["data"])
#             else:
#                 failed.append(result["error"])
        
#         # Cleanup temp files
#         await cleanup_temp_files(temp_files)
        
#         return BulkUploadResponse(
#             successful=successful,
#             failed=failed,
#             total_processed=len(files),
#             total_successful=len(successful),
#             total_failed=len(failed)
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")


# @router.get("/assignments", response_model=AssignmentList)
# async def list_assignments(teacher_id: str = None):
#     """
#     Get all uploaded assignments
#     """
#     try:
#         assignments = await get_all_assignments(teacher_id)
#         return AssignmentList(
#             assignments=assignments,
#             total=len(assignments)
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
# async def get_assignment(assignment_id: str):
#     """
#     Get specific assignment details
#     """
#     try:
#         from app.services.db_service import get_assignment_by_id
#         assignment = await get_assignment_by_id(assignment_id)
#         if not assignment:
#             raise HTTPException(status_code=404, detail="Assignment not found")
#         return assignment
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))







# from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
# from typing import List, Optional
# from app.services.file_processor import process_uploaded_file, cleanup_temp_files
# from app.services.s3_service import upload_to_s3
# from app.services.ocr_service import extract_text_from_file
# from app.services.db_service import save_assignment, get_all_assignments
# from app.models.assignment import (
#     AssignmentResponse, 
#     AssignmentList,
#     BulkUploadResponse, 
#     FailedUpload
# )
# import uuid
# from datetime import datetime
# import asyncio

# router = APIRouter()

# # @router.post("/assignments/upload", response_model=AssignmentResponse)
# # async def upload_assignment(
# #     file: UploadFile = File(...),
# #     title: str = Form(...),
# #     subject: str = Form(None),
# #     teacher_id: str = Form(...)
# # ):
# #     """
# #     Upload a single assignment (PDF, image, DOCX, etc.)
# #     """
# #     try:
# #         assignment_id = str(uuid.uuid4())
# #         temp_path = await process_uploaded_file(file, assignment_id)
# #         s3_url = await upload_to_s3(temp_path, assignment_id, file.filename)
# #         pages_data = await extract_text_from_file(temp_path)
        
# #         assignment_data = {
# #             "id": assignment_id,
# #             "title": title,
# #             "subject": subject,
# #             "teacher_id": teacher_id,
# #             "file_url": s3_url,
# #             "file_name": file.filename,
# #             "file_type": file.content_type,
# #             "pages": pages_data,
# #             "total_pages": len(pages_data),
# #             "full_text": " ".join([page["content"] for page in pages_data]),
# #             "upload_date": datetime.utcnow(),
# #             "status": "processed"
# #         }
        
# #         await save_assignment(assignment_data)
        
# #         from app.services.file_processor import cleanup_temp_file
# #         cleanup_temp_file(temp_path)
        
# #         return AssignmentResponse(
# #             id=assignment_id,
# #             title=title,
# #             subject=subject,
# #             teacher_id=teacher_id,
# #             file_url=s3_url,
# #             total_pages=len(pages_data),
# #             upload_date=assignment_data["upload_date"],
# #             status="processed"
# #         )
        
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# @router.post("/assignments/upload-multiple", response_model=BulkUploadResponse)
# async def upload_multiple_assignments(
#     files: List[UploadFile] = File(..., description="Upload multiple files"),
#     titles: List[str] = Query(..., description="Titles for each file (add multiple times)"),
#     teacher_ids: List[str] = Query(..., description="Teacher IDs for each file (add multiple times)"),
#     subjects: List[Optional[str]] = Query(None, description="Subjects for each file (optional, add multiple times)")
# ):
#     """
#     Upload multiple assignments at once.
    
#     How to use in Swagger UI:
#     1. Add files (click "Add string item" for each file)
#     2. Add titles as query params (click "Add string item" for each title)
#     3. Add teacher_ids as query params (click "Add string item" for each teacher_id)
#     4. Add subjects as query params (optional, click "Add string item" for each subject)
    
#     Example URL:
#     POST /assignments/upload-multiple?titles=History&titles=Math&titles=English&teacher_ids=123&teacher_ids=456&teacher_ids=678&subjects=History&subjects=Mathematics&subjects=English
    
#     Note: Number of titles and teacher_ids must match number of files.
#     Subjects is optional but if provided, must match number of files.
#     """
#     try:
#         # Validate input
#         if len(titles) != len(files):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Number of titles ({len(titles)}) must match number of files ({len(files)})"
#             )
        
#         if len(teacher_ids) != len(files):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Number of teacher_ids ({len(teacher_ids)}) must match number of files ({len(files)})"
#             )
        
#         # Handle subjects - if None or empty, create list of None
#         if not subjects or all(s is None or s == "" for s in subjects):
#             subjects = [None] * len(files)
#         elif len(subjects) != len(files):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Number of subjects ({len(subjects)}) must match number of files ({len(files)})"
#             )
        
#         successful = []
#         failed = []
#         temp_files = []
        
#         # Process each file
#         async def process_single_file(file: UploadFile, title: str, teacher_id: str, subject: Optional[str], index: int):
#             temp_path = None
#             try:
#                 assignment_id = str(uuid.uuid4())
#                 temp_path = await process_uploaded_file(file, assignment_id)
#                 temp_files.append(temp_path)
                
#                 s3_url = await upload_to_s3(temp_path, assignment_id, file.filename)
#                 pages_data = await extract_text_from_file(temp_path)
                
#                 assignment_data = {
#                     "id": assignment_id,
#                     "title": title,
#                     "subject": subject,
#                     "teacher_id": teacher_id,
#                     "file_url": s3_url,
#                     "file_name": file.filename,
#                     "file_type": file.content_type,
#                     "pages": pages_data,
#                     "total_pages": len(pages_data),
#                     "full_text": " ".join([page["content"] for page in pages_data]),
#                     "upload_date": datetime.utcnow(),
#                     "status": "processed"
#                 }
                
#                 await save_assignment(assignment_data)
                
#                 return {
#                     "success": True,
#                     "data": AssignmentResponse(
#                         id=assignment_id,
#                         title=title,
#                         subject=subject,
#                         teacher_id=teacher_id,
#                         file_url=s3_url,
#                         total_pages=len(pages_data),
#                         upload_date=assignment_data["upload_date"],
#                         status="processed"
#                     )
#                 }
#             except Exception as e:
#                 return {
#                     "success": False,
#                     "error": FailedUpload(
#                         file_name=file.filename,
#                         error=str(e)
#                     )
#                 }
        
#         # Process all files concurrently
#         tasks = [
#             process_single_file(file, title, teacher_id, subject, idx)
#             for idx, (file, title, teacher_id, subject) in enumerate(zip(files, titles, teacher_ids, subjects))
#         ]
#         results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         # Separate successful uploads from failures
#         for result in results:
#             if isinstance(result, Exception):
#                 failed.append(FailedUpload(file_name="unknown", error=str(result)))
#             elif result["success"]:
#                 successful.append(result["data"])
#             else:
#                 failed.append(result["error"])
        
#         # Cleanup temp files
#         await cleanup_temp_files(temp_files)
        
#         return BulkUploadResponse(
#             successful=successful,
#             failed=failed,
#             total_processed=len(files),
#             total_successful=len(successful),
#             total_failed=len(failed)
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")


# @router.get("/assignments", response_model=AssignmentList)
# async def list_assignments(teacher_id: str = None):
#     """
#     Get all uploaded assignments
#     """
#     try:
#         assignments = await get_all_assignments(teacher_id)
#         return AssignmentList(
#             assignments=assignments,
#             total=len(assignments)
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
# async def get_assignment(assignment_id: str):
#     """
#     Get specific assignment details
#     """
#     try:
#         from app.services.db_service import get_assignment_by_id
#         assignment = await get_assignment_by_id(assignment_id)
#         if not assignment:
#             raise HTTPException(status_code=404, detail="Assignment not found")
#         return assignment
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))









#################last er taoo valo chilo
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import List, Optional
from app.services.file_processor import process_uploaded_file, cleanup_temp_files
from app.services.s3_service import upload_to_s3
from app.services.ocr_service import extract_text_from_file
from app.services.db_service import save_assignment, get_all_assignments
from app.models.assignment import (
    AssignmentResponse, 
    AssignmentList,
    BulkUploadResponse, 
    FailedUpload
)
import uuid
from datetime import datetime
import asyncio

router = APIRouter()


@router.post("/assignments/upload-multiple", response_model=BulkUploadResponse)
async def upload_multiple_assignments(
    files: List[UploadFile] = File(..., description="Upload multiple files"),
    titles: List[str] = Query(..., description="Titles for each file (add multiple times)"),
    teacher_ids: List[str] = Query(..., description="Teacher IDs for each file (add multiple times)"),
    subjects: List[Optional[str]] = Query(None, description="Subjects for each file (optional, add multiple times)")
):
    """
    Upload multiple assignments at once with OCR on every page.
    """
    try:
        # Validate input
        if len(titles) != len(files):
            raise HTTPException(
                status_code=400, 
                detail=f"Number of titles ({len(titles)}) must match number of files ({len(files)})"
            )
        
        if len(teacher_ids) != len(files):
            raise HTTPException(
                status_code=400, 
                detail=f"Number of teacher_ids ({len(teacher_ids)}) must match number of files ({len(files)})"
            )
        
        # Handle subjects
        if not subjects or all(s is None or s == "" for s in subjects):
            subjects = [None] * len(files)
        elif len(subjects) != len(files):
            raise HTTPException(
                status_code=400, 
                detail=f"Number of subjects ({len(subjects)}) must match number of files ({len(files)})"
            )
        
        successful = []
        failed = []
        temp_files = []
        
        # Process each file
        async def process_single_file(file: UploadFile, title: str, teacher_id: str, subject: Optional[str], index: int):
            temp_path = None
            try:
                assignment_id = str(uuid.uuid4())
                
                print(f"\n{'='*60}")
                print(f"📤 [{index+1}/{len(files)}] Processing: {file.filename}")
                print(f"   Title: {title}")
                print(f"   Subject: {subject}")
                print(f"   Teacher ID: {teacher_id}")
                print(f"{'='*60}")
                
                # Save temp file
                temp_path = await process_uploaded_file(file, assignment_id)
                temp_files.append(temp_path)
                print(f"✅ Temp file saved: {temp_path}")
                
                # Upload to S3
                s3_url = await upload_to_s3(temp_path, assignment_id, file.filename)
                print(f"✅ Uploaded to S3: {s3_url}")
                
                # Extract text with OCR - THIS IS THE CRITICAL PART
                print(f"🔍 Starting OCR extraction...")
                pages_data = await extract_text_from_file(temp_path)
                
                # Verify OCR results
                if not pages_data or len(pages_data) == 0:
                    raise Exception(f"OCR failed - no pages extracted from {file.filename}")
                
                print(f"✅ OCR Complete! Extracted {len(pages_data)} pages:")
                for page in pages_data:
                    print(f"   📄 Page {page['page_number']}: {len(page['content'])} chars, method: {page['extraction_method']}")
                
                # Create assignment data
                assignment_data = {
                    "id": assignment_id,
                    "title": title,
                    "subject": subject,
                    "teacher_id": teacher_id,
                    "file_url": s3_url,
                    "file_name": file.filename,
                    "file_type": file.content_type,
                    "pages": pages_data,  # CRITICAL: Must have OCR data
                    "total_pages": len(pages_data),
                    "full_text": " ".join([page["content"] for page in pages_data]),
                    "upload_date": datetime.utcnow(),
                    "status": "processed"
                }
                
                # Verify full_text is not empty
                if not assignment_data["full_text"].strip():
                    print(f"⚠️  WARNING: full_text is empty for {file.filename}")
                else:
                    print(f"✅ full_text length: {len(assignment_data['full_text'])} chars")
                
                # Save to database
                print(f"💾 Saving to MongoDB...")
                await save_assignment(assignment_data)
                print(f"✅ Saved to MongoDB successfully")
                
                response = AssignmentResponse(
                    id=assignment_id,
                    title=title,
                    subject=subject,
                    teacher_id=teacher_id,
                    file_url=s3_url,
                    total_pages=len(pages_data),
                    upload_date=assignment_data["upload_date"],
                    status="processed"
                )
                
                print(f"✅ [{index+1}/{len(files)}] SUCCESS: {file.filename}\n")
                
                return {
                    "success": True,
                    "data": response
                }
                
            except Exception as e:
                print(f"❌ [{index+1}/{len(files)}] FAILED: {file.filename}")
                print(f"   Error: {str(e)}\n")
                return {
                    "success": False,
                    "error": FailedUpload(
                        file_name=file.filename,
                        error=str(e)
                    )
                }
        
        # Process files SEQUENTIALLY (not concurrent) to avoid issues
        print(f"\n🚀 Starting batch upload of {len(files)} files...")
        results = []
        for idx, (file, title, teacher_id, subject) in enumerate(zip(files, titles, teacher_ids, subjects)):
            result = await process_single_file(file, title, teacher_id, subject, idx)
            results.append(result)
        
        # Separate successful uploads from failures
        for result in results:
            if isinstance(result, Exception):
                failed.append(FailedUpload(file_name="unknown", error=str(result)))
            elif result["success"]:
                successful.append(result["data"])
            else:
                failed.append(result["error"])
        
        # Cleanup temp files
        print(f"🧹 Cleaning up {len(temp_files)} temp files...")
        await cleanup_temp_files(temp_files)
        print(f"✅ Cleanup complete")
        
        print(f"\n{'='*60}")
        print(f"📊 BATCH UPLOAD SUMMARY")
        print(f"   Total Processed: {len(files)}")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")
        print(f"{'='*60}\n")
        
        return BulkUploadResponse(
            successful=successful,
            failed=failed,
            total_processed=len(files),
            total_successful=len(successful),
            total_failed=len(failed)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ CRITICAL ERROR in bulk upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")


@router.get("/assignments", response_model=AssignmentList)
async def list_assignments(teacher_id: str = None):
    """
    Get all uploaded assignments
    """
    try:
        assignments = await get_all_assignments(teacher_id)
        return AssignmentList(
            assignments=assignments,
            total=len(assignments)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(assignment_id: str):
    """
    Get specific assignment details
    """
    try:
        from app.services.db_service import get_assignment_by_id
        assignment = await get_assignment_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return assignment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))