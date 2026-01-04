from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from app.services.mindmap_service import generate_mindmap_data

router = APIRouter()


class MindMapRequest(BaseModel):
    prompt: str
    student_id: str = None
    format: str = "png"  # png or svg


class MindMapResponse(BaseModel):
    s3_url: str  # Primary URL to S3 hosted image
    image_url: str  # Same as s3_url for compatibility
    topic: str
    total_nodes: int
    format: str


@router.post("/mindmap/generate", response_model=MindMapResponse)
async def generate_mindmap(request: MindMapRequest):
    """
    Generate a colorful mind map IMAGE and upload to S3
    
    Returns S3 URL for the uploaded image
    
    Example prompts:
    - "Photosynthesis process"
    - "Types of programming languages"
    - "Solar system planets"
    - "Machine learning algorithms"
    """
    try:
        if not request.prompt or len(request.prompt.strip()) < 3:
            raise HTTPException(
                status_code=400, 
                detail="Prompt must be at least 3 characters long"
            )
        
        # Validate format
        if request.format not in ["png", "svg"]:
            raise HTTPException(
                status_code=400,
                detail="Format must be 'png' or 'svg'"
            )
        
        print(f"🧠 Generating mind map IMAGE for: {request.prompt}")
        print(f"👤 Student ID: {request.student_id or 'N/A'}")
        
        # Generate mind map and upload to S3
        mindmap_data = await generate_mindmap_data(
            prompt=request.prompt,
            student_id=request.student_id,
            format=request.format,
            upload_to_s3=True
        )
        
        print(f"✅ Mind map uploaded! URL: {mindmap_data['s3_url']}")
        print(f"📊 Total nodes: {mindmap_data['total_nodes']}")
        
        return MindMapResponse(
            s3_url=mindmap_data['s3_url'],
            image_url=mindmap_data['image_url'],
            topic=mindmap_data['topic'],
            total_nodes=mindmap_data['total_nodes'],
            format=mindmap_data['format']
        )
        
    except Exception as e:
        print(f"❌ Mind map generation error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Mind map generation failed: {str(e)}"
        )


@router.get("/mindmap/example")
async def get_example_mindmap():
    """Get an example mind map image uploaded to S3"""
    try:
        example_prompt = "Python Programming Basics"
        mindmap_data = await generate_mindmap_data(
            prompt=example_prompt,
            student_id="example",
            format="png",
            upload_to_s3=True
        )
        
        return MindMapResponse(
            s3_url=mindmap_data['s3_url'],
            image_url=mindmap_data['image_url'],
            topic=mindmap_data['topic'],
            total_nodes=mindmap_data['total_nodes'],
            format=mindmap_data['format']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))