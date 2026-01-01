from fastapi import UploadFile
import os
import shutil
import aiofiles
from app.config import settings

async def process_uploaded_file(file: UploadFile, assignment_id: str) -> str:
    """
    Save uploaded file temporarily (async version for better performance)
    """
    # Get file extension
    file_extension = os.path.splitext(file.filename)[1]
    
    # Create temp file path
    temp_path = os.path.join(settings.UPLOAD_DIR, f"{assignment_id}{file_extension}")
    
    # Save file asynchronously
    async with aiofiles.open(temp_path, "wb") as buffer:
        content = await file.read()
        await buffer.write(content)
    
    return temp_path


def cleanup_temp_file(file_path: str):
    """
    Delete temporary file
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Failed to cleanup file {file_path}: {e}")


async def cleanup_temp_files(file_paths: list):
    """
    Delete multiple temporary files (for bulk uploads)
    """
    for file_path in file_paths:
        cleanup_temp_file(file_path)