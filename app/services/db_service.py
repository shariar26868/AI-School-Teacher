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
    """
    Save assignment to MongoDB with smart chunking for large content
    """
    collection = database["assignments"]
    
    full_text = assignment_data.get('full_text', '')
    
    # Debug logging
    print(f"\n{'='*60}")
    print(f"💾 SAVING TO MONGODB")
    print(f"   Assignment ID: {assignment_data.get('id')}")
    print(f"   Full text length BEFORE save: {len(full_text)} characters")
    print(f"   Total pages: {assignment_data.get('total_pages')}")
    print(f"{'='*60}")
    
    # Chunking strategy for large text (anything over 100KB)
    chunk_size = 100000  # 100KB per chunk
    
    if len(full_text) > chunk_size:
        print(f"⚠️  Large content detected! Using chunking strategy...")
        
        # Split into chunks
        chunks = []
        for i in range(0, len(full_text), chunk_size):
            chunk = full_text[i:i + chunk_size]
            chunks.append(chunk)
        
        # Store chunks separately
        assignment_data['full_text_chunks'] = chunks
        assignment_data['full_text'] = full_text[:2000]  # Keep 2KB preview
        assignment_data['is_chunked'] = True
        assignment_data['total_chunks'] = len(chunks)
        assignment_data['original_text_length'] = len(full_text)
        
        print(f"✅ Content split into {len(chunks)} chunks")
        print(f"   Preview stored: {len(assignment_data['full_text'])} chars")
        print(f"   Full content in chunks: {assignment_data['original_text_length']} chars")
    else:
        # For smaller content, store directly
        assignment_data['is_chunked'] = False
        assignment_data['original_text_length'] = len(full_text)
        print(f"✅ Content stored directly (no chunking needed)")
    
    # Ensure proper encoding
    if 'full_text' in assignment_data:
        assignment_data['full_text'] = str(assignment_data['full_text'])
    
    # Insert into MongoDB
    result = await collection.insert_one(assignment_data)
    
    # Verify what was actually saved
    print(f"\n{'='*60}")
    print(f"🔍 VERIFYING SAVED DATA")
    saved_doc = await collection.find_one({"_id": result.inserted_id})
    
    if saved_doc:
        saved_full_text_length = len(saved_doc.get('full_text', ''))
        is_chunked = saved_doc.get('is_chunked', False)
        
        print(f"   ✅ Document saved successfully")
        print(f"   ID: {saved_doc.get('id')}")
        print(f"   Full text preview length: {saved_full_text_length} chars")
        print(f"   Is chunked: {is_chunked}")
        
        if is_chunked:
            total_chunks = saved_doc.get('total_chunks', 0)
            original_length = saved_doc.get('original_text_length', 0)
            chunks = saved_doc.get('full_text_chunks', [])
            actual_chunks_length = sum(len(chunk) for chunk in chunks)
            
            print(f"   Total chunks: {total_chunks}")
            print(f"   Original length: {original_length} chars")
            print(f"   Actual chunks total: {actual_chunks_length} chars")
            
            if actual_chunks_length != original_length:
                print(f"   ⚠️  WARNING: Chunk length mismatch!")
            else:
                print(f"   ✅ All content successfully saved in chunks")
        else:
            if saved_full_text_length != len(full_text):
                print(f"   ⚠️  WARNING: Text truncation detected!")
                print(f"   Expected: {len(full_text)} chars")
                print(f"   Actual: {saved_full_text_length} chars")
            else:
                print(f"   ✅ Full text saved completely")
    else:
        print(f"   ❌ ERROR: Could not verify saved document")
    
    print(f"{'='*60}\n")


async def get_all_assignments(teacher_id: Optional[str] = None) -> List[dict]:
    """
    Get all assignments with full text reconstruction
    """
    collection = database["assignments"]
    
    query = {"teacher_id": teacher_id} if teacher_id else {}
    
    cursor = collection.find(query).sort("upload_date", -1)
    assignments = await cursor.to_list(length=100)
    
    # Process each assignment
    for assignment in assignments:
        assignment["_id"] = str(assignment["_id"])
        
        # Reconstruct full text if chunked
        if assignment.get('is_chunked', False):
            chunks = assignment.get('full_text_chunks', [])
            full_text = ''.join(chunks)
            assignment['full_text'] = full_text
            # Remove chunks from response to save bandwidth
            assignment.pop('full_text_chunks', None)
    
    return assignments


async def get_assignment_by_id(assignment_id: str) -> Optional[dict]:
    """
    Get specific assignment with full text reconstruction
    """
    collection = database["assignments"]
    assignment = await collection.find_one({"id": assignment_id})
    
    if assignment:
        assignment["_id"] = str(assignment["_id"])
        
        # Reconstruct full text if chunked
        if assignment.get('is_chunked', False):
            chunks = assignment.get('full_text_chunks', [])
            full_text = ''.join(chunks)
            
            print(f"\n{'='*60}")
            print(f"📖 RECONSTRUCTING CHUNKED CONTENT")
            print(f"   Assignment ID: {assignment_id}")
            print(f"   Total chunks: {len(chunks)}")
            print(f"   Reconstructed length: {len(full_text)} chars")
            print(f"   Original length: {assignment.get('original_text_length')} chars")
            print(f"{'='*60}\n")
            
            assignment['full_text'] = full_text
            # Remove chunks from response
            assignment.pop('full_text_chunks', None)
    
    return assignment


async def get_assignment_full_text(assignment_id: str) -> Optional[str]:
    """
    Get ONLY the full text of an assignment (optimized for AI processing)
    """
    collection = database["assignments"]
    assignment = await collection.find_one(
        {"id": assignment_id},
        {"full_text": 1, "full_text_chunks": 1, "is_chunked": 1, "_id": 0}
    )
    
    if not assignment:
        return None
    
    # Reconstruct if chunked
    if assignment.get('is_chunked', False):
        chunks = assignment.get('full_text_chunks', [])
        return ''.join(chunks)
    else:
        return assignment.get('full_text', '')


async def update_assignment_pages(assignment_id: str, pages_data: list):
    """
    Update pages data for an assignment (useful for re-processing)
    """
    collection = database["assignments"]
    
    full_text = " ".join([page["content"] for page in pages_data])
    
    update_data = {
        "pages": pages_data,
        "total_pages": len(pages_data),
        "full_text": full_text
    }
    
    # Apply chunking if needed
    if len(full_text) > 100000:
        chunks = []
        chunk_size = 100000
        for i in range(0, len(full_text), chunk_size):
            chunks.append(full_text[i:i + chunk_size])
        
        update_data['full_text_chunks'] = chunks
        update_data['full_text'] = full_text[:2000]
        update_data['is_chunked'] = True
        update_data['total_chunks'] = len(chunks)
        update_data['original_text_length'] = len(full_text)
    
    result = await collection.update_one(
        {"id": assignment_id},
        {"$set": update_data}
    )
    
    return result.modified_count > 0


async def delete_assignment(assignment_id: str) -> bool:
    """
    Delete an assignment
    """
    collection = database["assignments"]
    result = await collection.delete_one({"id": assignment_id})
    return result.deleted_count > 0


async def search_assignments(query: str, teacher_id: Optional[str] = None) -> List[dict]:
    """
    Search assignments by text content (works with chunked content too)
    """
    collection = database["assignments"]
    
    # Build search query
    search_query = {
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"subject": {"$regex": query, "$options": "i"}},
            {"full_text": {"$regex": query, "$options": "i"}}
        ]
    }
    
    if teacher_id:
        search_query["teacher_id"] = teacher_id
    
    cursor = collection.find(search_query).sort("upload_date", -1)
    assignments = await cursor.to_list(length=50)
    
    # Reconstruct full text if needed
    for assignment in assignments:
        assignment["_id"] = str(assignment["_id"])
        
        if assignment.get('is_chunked', False):
            chunks = assignment.get('full_text_chunks', [])
            assignment['full_text'] = ''.join(chunks)
            assignment.pop('full_text_chunks', None)
    
    return assignments


async def get_database_stats() -> dict:
    """
    Get database statistics
    """
    collection = database["assignments"]
    
    total_assignments = await collection.count_documents({})
    chunked_assignments = await collection.count_documents({"is_chunked": True})
    
    # Calculate total storage
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_text_length": {"$sum": "$original_text_length"}
            }
        }
    ]
    
    result = await collection.aggregate(pipeline).to_list(length=1)
    total_text_length = result[0]['total_text_length'] if result else 0
    
    return {
        "total_assignments": total_assignments,
        "chunked_assignments": chunked_assignments,
        "direct_storage_assignments": total_assignments - chunked_assignments,
        "total_text_length": total_text_length,
        "total_text_size_mb": round(total_text_length / (1024 * 1024), 2)
    }
