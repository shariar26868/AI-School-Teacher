from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # OpenAI (optional - only needed if not using Gemini for everything)
    OPENAI_API_KEY: Optional[str] = None
    
    # Google Gemini (for mindmap and other AI tasks)
    GEMINI_API_KEY: Optional[str] = None
    
    # FAL AI (for image generation)
    FAL_KEY: Optional[str] = None

    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str
    
    # MongoDB
    MONGODB_URI: str
    DATABASE_NAME: str
    
    # YouTube
    YOUTUBE_API_KEY: str
    
    # App
    UPLOAD_DIR: str = "temp"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    
    class Config:
        env_file = ".env"
        extra = 'ignore'

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()



# fal-ai/ideogram - fal api model 