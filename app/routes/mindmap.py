



from fastapi import APIRouter, HTTPException
from typing import Optional
from bson import ObjectId
from app.models.mindmap import MindMapRequest, MindMapResponse
from app.services.mindmap_service import generate_mindmap_data

router = APIRouter()


@router.post("/mindmap/generate", response_model=MindMapResponse)
async def generate_mindmap(request: MindMapRequest):
    """
    Generate a mind map image and save to MongoDB.
    Returns base64 image + mongo_id.
    """
    try:
        if not request.prompt or len(request.prompt.strip()) < 3:
            raise HTTPException(status_code=400, detail="Prompt must be at least 3 characters")
        if request.format not in ["png", "svg"]:
            raise HTTPException(status_code=400, detail="Format must be 'png' or 'svg'")

        print(f"Generating mind map for: {request.prompt}")

        mindmap_data = await generate_mindmap_data(
            prompt=request.prompt,
            student_id=request.student_id,
            format=request.format,
        )

        print(f"Done! Topic: {mindmap_data['topic']} | Theme: {mindmap_data.get('theme')} | Mongo ID: {mindmap_data.get('mongo_id')}")

        return MindMapResponse(
            image_url=mindmap_data["image_url"],
            image_base64=mindmap_data.get("image_base64"),
            topic=mindmap_data["topic"],
            total_nodes=mindmap_data["total_nodes"],
            format=mindmap_data["format"],
            theme=mindmap_data.get("theme"),
            mongo_id=mindmap_data.get("mongo_id"),
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Mind map generation failed: {str(e)}")


@router.get("/mindmap/history/{student_id}")
async def get_student_mindmaps(student_id: str, limit: int = 20):
    """
    Get all mindmaps for a student (without image data for speed).
    """
    try:
        from app.database import database as db

        cursor = db["mindmaps"].find(
            {"student_id": student_id},
            {"image_base64": 0}
        ).sort("created_at", -1).limit(limit)

        maps = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if doc.get("created_at"):
                doc["created_at"] = doc["created_at"].isoformat()
            maps.append(doc)

        return {"student_id": student_id, "mindmaps": maps, "count": len(maps)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mindmap/{mongo_id}")
async def get_mindmap_by_id(mongo_id: str):
    """
    Get a specific mindmap with full image by MongoDB ID.
    """
    try:
        from app.database import database as db

        doc = await db["mindmaps"].find_one({"_id": ObjectId(mongo_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Mind map not found")

        return {
            "mongo_id": str(doc["_id"]),
            "topic": doc["topic"],
            "prompt": doc.get("prompt"),
            "theme": doc.get("theme"),
            "total_nodes": doc["total_nodes"],
            "image_base64": doc["image_base64"],
            "image_url": f"data:image/png;base64,{doc['image_base64']}",
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/mindmap/{mongo_id}")
async def delete_mindmap(mongo_id: str):
    """Delete a mindmap by MongoDB ID."""
    try:
        from app.database import database as db

        result = await db["mindmaps"].delete_one({"_id": ObjectId(mongo_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Mind map not found")
        return {"message": "Mind map deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))