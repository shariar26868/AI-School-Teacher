

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
from app.services.db_service import get_assignment_by_id, save_video_links, get_video_links
from app.services.chatbot_service import (
    answer_question,
    should_suggest_videos,
    search_youtube_videos,
    generate_search_query,
    clear_conversation,
    get_conversation_history,
    get_greeting_response,
    handle_ai_response,
    handle_user_continuation
)

router = APIRouter()


class QuestionRequest(BaseModel):
    assignment_id: str
    student_id: str
    question: str
    interaction_type: Literal["greeting", "ai_response", "user_question"] = "ai_response"
    previous_ai_response: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    video_links: list = []
    assignment_title: str
    should_show_videos: bool = False
    interaction_type: str = "ai_response"


# ─────────────────────────────────────────────
# MAIN CHAT ENDPOINT
# ─────────────────────────────────────────────

@router.post("/chatbot/ask", response_model=ChatResponse)
async def ask_question(request: QuestionRequest):
    try:
        assignment = await get_assignment_by_id(request.assignment_id)

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        assignment_context = assignment.get('full_text', '')
        assignment_title   = assignment.get('title', 'Untitled Assignment')

        # ── Greeting ──
        if request.interaction_type == "greeting":
            answer = get_greeting_response(assignment_title)
            return ChatResponse(
                answer=answer,
                video_links=[],
                assignment_title=assignment_title,
                should_show_videos=False,
                interaction_type="greeting"
            )

        # ── AI Response ──
        elif request.interaction_type == "ai_response":
            answer = await handle_ai_response(
                question=request.question,
                assignment_context=assignment_context,
                assignment_title=assignment_title,
                student_id=request.student_id,
                assignment_id=request.assignment_id
            )

            history = await get_conversation_history(request.student_id, request.assignment_id)
            suggest_videos = await should_suggest_videos(request.question, answer, history)

            video_links = []
            if suggest_videos:
                print(f"🎥 Searching YouTube videos...")
                search_query = await generate_search_query(
                    request.question, answer, assignment_context
                )
                print(f"   Search query: {search_query}")
                video_links = await search_youtube_videos(search_query, max_results=3)

                # ── Video links save করো ──
                if video_links:
                    print(f"   ✅ Found {len(video_links)} videos — saving to DB...")
                    await save_video_links(
                        student_id=request.student_id,
                        assignment_id=request.assignment_id,
                        question=request.question,
                        video_links=video_links
                    )
                else:
                    print(f"   ⚠️  No videos found")
            else:
                print(f"💬 Conversational response — no videos suggested")

            return ChatResponse(
                answer=answer,
                video_links=video_links,
                assignment_title=assignment_title,
                should_show_videos=suggest_videos,
                interaction_type="ai_response"
            )

        # ── User Continuation ──
        elif request.interaction_type == "user_question":
            answer = await handle_user_continuation(
                user_input=request.question,
                previous_ai_response=request.previous_ai_response,
                assignment_context=assignment_context,
                assignment_title=assignment_title,
                student_id=request.student_id,
                assignment_id=request.assignment_id
            )

            return ChatResponse(
                answer=answer,
                video_links=[],
                assignment_title=assignment_title,
                should_show_videos=False,
                interaction_type="user_question"
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid interaction_type")

    except Exception as e:
        print(f"❌ Chatbot error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Alias
@router.post("/chat", response_model=ChatResponse)
async def ask_question_short(request: QuestionRequest):
    return await ask_question(request)


# ─────────────────────────────────────────────
# VIDEO LINKS GET ENDPOINT
# ─────────────────────────────────────────────

@router.get("/chatbot/videos/{student_id}/{assignment_id}")
async def get_student_video_links(student_id: str, assignment_id: str):
    """
    Student এর সব saved video links আনো
    Website এ show করার জন্য
    """
    try:
        videos = await get_video_links(student_id, assignment_id)
        return {
            "student_id": student_id,
            "assignment_id": assignment_id,
            "total": len(videos),
            "videos": videos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# CLEAR HISTORY
# ─────────────────────────────────────────────

@router.post("/chatbot/clear")
async def clear_chat_history(student_id: str, assignment_id: str):
    try:
        await clear_conversation(student_id, assignment_id)
        return {
            "message": "Conversation cleared successfully",
            "student_id": student_id,
            "assignment_id": assignment_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# CHAT HISTORY
# ─────────────────────────────────────────────

@router.get("/chatbot/history/{student_id}/{assignment_id}")
async def get_chat_history(student_id: str, assignment_id: str):
    try:
        history = await get_conversation_history(student_id, assignment_id)

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