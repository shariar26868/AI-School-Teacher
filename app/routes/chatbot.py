from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.db_service import get_assignment_by_id
from app.services.chatbot_service import (
    answer_question, 
    should_suggest_videos,
    search_youtube_videos,
    generate_search_query,
    clear_conversation,
    get_conversation_history
)

router = APIRouter()


class QuestionRequest(BaseModel):
    assignment_id: str
    student_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    video_links: list = []
    assignment_title: str
    should_show_videos: bool = False


# Main endpoint - works with /api/chatbot/ask
@router.post("/chatbot/ask", response_model=ChatResponse)
async def ask_question(request: QuestionRequest):
    """
    Natural conversational chatbot
    - Greets on first message
    - Gives hints first
    - Full solution only when requested
    - YouTube videos suggested after solution
    """
    try:
        # Get assignment
        assignment = await get_assignment_by_id(request.assignment_id)
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        assignment_context = assignment.get('full_text', '')
        assignment_title = assignment.get('title', 'Untitled Assignment')
        
        # Get conversation history
        history = get_conversation_history(request.student_id, request.assignment_id)
        
        # Get AI response
        answer = await answer_question(
            question=request.question,
            assignment_context=assignment_context,
            assignment_title=assignment_title,
            student_id=request.student_id,
            assignment_id=request.assignment_id
        )
        
        # Check if we should suggest videos
        suggest_videos = await should_suggest_videos(
            request.question, 
            answer,
            history
        )
        
        video_links = []
        
        if suggest_videos:
            print(f"🎥 Full solution provided! Searching YouTube videos...")
            
            # Generate search query
            search_query = await generate_search_query(
                request.question,
                answer,
                assignment_context
            )
            
            print(f"   Search query: {search_query}")
            
            # Search YouTube
            video_links = await search_youtube_videos(search_query, max_results=3)
            
            if video_links:
                print(f"   ✅ Found {len(video_links)} videos")
            else:
                print(f"   ⚠️  No videos found")
        else:
            print(f"💬 Conversational response - no videos suggested yet")
        
        return ChatResponse(
            answer=answer,
            video_links=video_links,
            assignment_title=assignment_title,
            should_show_videos=suggest_videos
        )
        
    except Exception as e:
        print(f"❌ Chatbot error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")


# Shorter alias endpoint - works with /api/chat
@router.post("/chat", response_model=ChatResponse)
async def ask_question_short(request: QuestionRequest):
    """
    Alias for /chatbot/ask endpoint
    Allows shorter URL: /api/chat
    """
    return await ask_question(request)


@router.post("/chatbot/clear")
async def clear_chat_history(
    student_id: str,
    assignment_id: str
):
    """Clear conversation history - start fresh"""
    try:
        clear_conversation(student_id, assignment_id)
        
        return {
            "message": "Conversation cleared successfully",
            "student_id": student_id,
            "assignment_id": assignment_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chatbot/history/{student_id}/{assignment_id}")
async def get_chat_history(student_id: str, assignment_id: str):
    """Get conversation history"""
    try:
        history = get_conversation_history(student_id, assignment_id)
        
        # Format for display
        formatted_history = []
        for msg in history:
            formatted_history.append({
                "role": msg["role"],
                "message": msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"],
                "full_message": msg["content"]
            })
        
        return {
            "student_id": student_id,
            "assignment_id": assignment_id,
            "total_messages": len(history),
            "conversation": formatted_history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))