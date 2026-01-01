from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.chatbot_service import answer_question
from app.services.video_search import search_videos
from app.services.db_service import get_assignment_by_id

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    Ask questions about an assignment and get AI-powered answers
    """
    try:
        # Get assignment from database
        assignment = await get_assignment_by_id(request.assignment_id)
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Get AI answer
        answer = await answer_question(
            question=request.question,
            assignment_context=assignment["full_text"],
            assignment_title=assignment["title"]
        )
        
        # Search for related videos
        video_links = await search_videos(request.question, assignment["subject"])
        
        return ChatResponse(
            answer=answer,
            video_links=video_links,
            assignment_title=assignment["title"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")