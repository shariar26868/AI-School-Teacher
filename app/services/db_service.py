from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from typing import Optional, List

# MongoDB client
mongodb_client: Optional[AsyncIOMotorClient] = None
database = None

async def connect_db():
    """Connect to MongoDB"""
    global mongodb_client, database
    mongodb_client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = mongodb_client[settings.DATABASE_NAME]


async def close_db():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()


async def save_assignment(assignment_data: dict):
    """Save assignment to MongoDB"""
    collection = database["assignments"]
    await collection.insert_one(assignment_data)


async def get_all_assignments(teacher_id: Optional[str] = None) -> List[dict]:
    """Get all assignments"""
    collection = database["assignments"]
    
    query = {"teacher_id": teacher_id} if teacher_id else {}
    
    cursor = collection.find(query).sort("upload_date", -1)
    assignments = await cursor.to_list(length=100)
    
    # Convert ObjectId to string
    for assignment in assignments:
        assignment["_id"] = str(assignment["_id"])
    
    return assignments


async def get_assignment_by_id(assignment_id: str) -> Optional[dict]:
    """Get specific assignment"""
    collection = database["assignments"]
    assignment = await collection.find_one({"id": assignment_id})
    
    if assignment:
        assignment["_id"] = str(assignment["_id"])
    
    return assignment



