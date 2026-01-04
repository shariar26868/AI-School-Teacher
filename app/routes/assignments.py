from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import List, Optional
from app.services.file_processor import process_uploaded_file, cleanup_temp_files
from app.services.s3_service import upload_to_s3
from app.services.ocr_service import extract_text_from_file
from app.services.db_service import save_assignment, get_all_assignments, get_assignment_by_id, get_assignment_full_text
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
                    print(f"✅ full_text length BEFORE save: {len(assignment_data['full_text'])} chars")
                
                # Save to database
                print(f"💾 Saving to MongoDB...")
                await save_assignment(assignment_data)
                print(f"✅ Saved to MongoDB successfully")
                
                # DEBUG: Immediate verification after save
                print(f"\n{'='*60}")
                print(f"🔍 IMMEDIATE VERIFICATION CHECK")
                print(f"{'='*60}")
                
                saved = await get_assignment_by_id(assignment_id)
                
                if saved:
                    saved_full_text_length = len(saved.get('full_text', ''))
                    is_chunked = saved.get('is_chunked', False)
                    original_length = saved.get('original_text_length', 0)
                    
                    print(f"✅ Assignment retrieved from DB")
                    print(f"   Assignment ID: {assignment_id}")
                    print(f"   Retrieved full_text length: {saved_full_text_length} chars")
                    print(f"   Is chunked: {is_chunked}")
                    print(f"   Original length (metadata): {original_length} chars")
                    print(f"   Expected length: {len(assignment_data['full_text'])} chars")
                    
                    # Check for data loss
                    if saved_full_text_length < len(assignment_data['full_text']) and not is_chunked:
                        print(f"\n   ⚠️⚠️⚠️  DATA LOSS DETECTED! ⚠️⚠️⚠️")
                        print(f"   Lost: {len(assignment_data['full_text']) - saved_full_text_length} chars")
                        print(f"   This is {((len(assignment_data['full_text']) - saved_full_text_length) / len(assignment_data['full_text']) * 100):.1f}% data loss!")
                    elif is_chunked:
                        # For chunked data, verify chunks
                        chunks = saved.get('full_text_chunks', [])
                        total_chunks_length = sum(len(chunk) for chunk in chunks)
                        print(f"   Total chunks: {len(chunks)}")
                        print(f"   Total chunks length: {total_chunks_length} chars")
                        
                        if total_chunks_length == len(assignment_data['full_text']):
                            print(f"   ✅ All content saved successfully in chunks!")
                        else:
                            print(f"   ⚠️  Chunk length mismatch!")
                    else:
                        print(f"   ✅ Full content saved successfully (no chunking needed)!")
                    
                    # Show preview
                    print(f"\n   📝 Content Preview:")
                    print(f"   First 200 chars: {saved.get('full_text', '')[:200]}")
                    print(f"   Last 200 chars: {saved.get('full_text', '')[-200:]}")
                    
                else:
                    print(f"   ❌ ERROR: Could not retrieve saved assignment from DB!")
                
                print(f"{'='*60}\n")
                
                # Create response with FULL TEXT included
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
                
                # Add full_text to response (convert to dict and add)
                response_dict = response.dict()
                response_dict["full_text"] = assignment_data["full_text"]
                response_dict["full_text_length"] = len(assignment_data["full_text"])
                response_dict["pages"] = pages_data
                
                print(f"✅ [{index+1}/{len(files)}] SUCCESS: {file.filename}\n")
                
                return {
                    "success": True,
                    "data": response_dict
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


@router.get("/assignments/{assignment_id}")
async def get_assignment(assignment_id: str):
    """
    Get specific assignment details with FULL TEXT
    """
    try:
        assignment = await get_assignment_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Add full_text_length to response
        if assignment.get('full_text'):
            assignment['full_text_length'] = len(assignment['full_text'])
        
        return assignment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/{assignment_id}/full-text")
async def get_assignment_full_text_endpoint(assignment_id: str):
    """
    Get ONLY the complete full text of an assignment (for viewing/debugging)
    """
    try:
        full_text = await get_assignment_full_text(assignment_id)
        
        if not full_text:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return {
            "assignment_id": assignment_id,
            "length": len(full_text),
            "content": full_text,
            "preview": {
                "first_200": full_text[:200],
                "last_200": full_text[-200:]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/{assignment_id}/pages")
async def get_assignment_pages(assignment_id: str):
    """
    Get page-by-page content of an assignment
    """
    try:
        assignment = await get_assignment_by_id(assignment_id)
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        pages = assignment.get('pages', [])
        
        return {
            "assignment_id": assignment_id,
            "title": assignment.get('title'),
            "total_pages": len(pages),
            "pages": pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))