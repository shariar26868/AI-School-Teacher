import boto3
from app.config import settings
import os
import asyncio
from functools import partial

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

# Semaphore to limit concurrent S3 uploads (max 10 at a time)
S3_SEMAPHORE = asyncio.Semaphore(10)

async def upload_to_s3(file_path: str, assignment_id: str, original_filename: str) -> str:
    """
    Upload file to S3 and return URL (with rate limiting)
    """
    async with S3_SEMAPHORE:
        file_extension = os.path.splitext(original_filename)[1]
        s3_key = f"assignments/{assignment_id}{file_extension}"
        
        # Run blocking S3 upload in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(
                s3_client.upload_file,
                file_path,
                settings.S3_BUCKET_NAME,
                s3_key,
                ExtraArgs={'ContentType': get_content_type(file_extension)}
            )
        )
        
        # Generate URL
        url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
        
        return url


def get_content_type(extension: str) -> str:
    """
    Get content type based on file extension
    """
    content_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain'
    }
    return content_types.get(extension.lower(), 'application/octet-stream')