import boto3
from app.config import settings
import os
import asyncio
from functools import partial
from datetime import datetime
import uuid
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

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


async def upload_mindmap_to_s3(
    image_bytes: bytes, 
    student_id: str = None,
    topic: str = None,
    format: str = "png"
) -> str:
    """
    Upload mind map image to S3 and return public URL
    
    Args:
        image_bytes: Image data in bytes
        student_id: Optional student ID
        topic: Topic name for filename
        format: Image format (png or svg)
    
    Returns:
        Public URL of uploaded image
    """
    async with S3_SEMAPHORE:
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            
            # Clean topic name for filename
            safe_topic = sanitize_filename(topic) if topic else "mindmap"
            
            # Create S3 key (path)
            if student_id:
                s3_key = f"mindmaps/{student_id}/{safe_topic}_{timestamp}_{unique_id}.{format}"
            else:
                s3_key = f"mindmaps/general/{safe_topic}_{timestamp}_{unique_id}.{format}"
            
            # Determine content type
            content_type = "image/svg+xml" if format == "svg" else "image/png"
            
            # Create BytesIO object from bytes
            file_obj = BytesIO(image_bytes)
            
            # Upload to S3 (run in thread pool to avoid blocking)
            # NOTE: ACL removed because bucket doesn't support ACLs
            # Bucket policy handles public access instead
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                partial(
                    s3_client.upload_fileobj,
                    file_obj,
                    settings.S3_BUCKET_NAME,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': 'max-age=31536000'  # Cache for 1 year
                    }
                )
            )
            
            # Generate public URL
            cloudfront_url = getattr(settings, 'CLOUDFRONT_URL', None)
            use_presigned_url = getattr(settings, 'USE_PRESIGNED_URLS', False)
            
            if use_presigned_url:
                # Generate presigned URL (valid for 7 days)
                public_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.S3_BUCKET_NAME,
                        'Key': s3_key
                    },
                    ExpiresIn=604800  # 7 days in seconds
                )
            elif cloudfront_url:
                public_url = f"{cloudfront_url}/{s3_key}"
            else:
                public_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            
            logger.info(f"✅ Mind map uploaded to S3: {s3_key}")
            return public_url
        
        except Exception as e:
            logger.error(f"❌ S3 upload error: {e}")
            raise Exception(f"Failed to upload mind map to S3: {str(e)}")


async def delete_mindmap_from_s3(s3_url: str) -> bool:
    """
    Delete mind map image from S3
    
    Args:
        s3_url: Full S3 URL of the image
    
    Returns:
        True if deleted successfully
    """
    async with S3_SEMAPHORE:
        try:
            # Extract S3 key from URL
            s3_key = extract_s3_key_from_url(s3_url)
            
            if not s3_key:
                logger.error(f"❌ Could not extract S3 key from URL: {s3_url}")
                return False
            
            # Delete object (run in thread pool)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                partial(
                    s3_client.delete_object,
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=s3_key
                )
            )
            
            logger.info(f"✅ Mind map deleted from S3: {s3_key}")
            return True
        
        except Exception as e:
            logger.error(f"❌ S3 delete error: {e}")
            return False


def get_content_type(extension: str) -> str:
    """
    Get content type based on file extension
    """
    content_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain'
    }
    return content_types.get(extension.lower(), 'application/octet-stream')


def sanitize_filename(filename: str) -> str:
    """Remove special characters from filename"""
    # Replace spaces and special chars with underscores
    safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in filename)
    # Limit length
    return safe_name[:50]


def extract_s3_key_from_url(url: str) -> str:
    """Extract S3 key from full URL"""
    try:
        # Handle CloudFront URL
        cloudfront_url = getattr(settings, 'CLOUDFRONT_URL', None)
        if cloudfront_url and url.startswith(cloudfront_url):
            return url.replace(f"{cloudfront_url}/", "")
        
        # Handle S3 URL
        bucket_url = f"{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/"
        if bucket_url in url:
            parts = url.split(bucket_url)
            if len(parts) > 1:
                return parts[1]
        
        # Handle alternative S3 URL format
        alt_bucket_url = f"s3.{settings.AWS_REGION}.amazonaws.com/{settings.S3_BUCKET_NAME}/"
        if alt_bucket_url in url:
            parts = url.split(alt_bucket_url)
            if len(parts) > 1:
                return parts[1]
        
        return None
    except Exception as e:
        logger.error(f"Error extracting S3 key: {e}")
        return None