

import httpx
import tempfile
import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from typing import Optional, List
from datetime import datetime

REMOTE_API_BASE = "http://206.162.244.131:5021/api/v1"
TIMEOUT = 60

# MongoDB client (for chat messages + OCR cache + video links)
mongodb_client = None
database = None


def _normalize(data: dict) -> dict:
    if data and "_id" in data:
        data["_id"] = str(data["_id"])
    return data


# ─────────────────────────────────────────────
# DB Connection
# ─────────────────────────────────────────────

async def connect_db():
    global mongodb_client, database
    mongodb_client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = mongodb_client[settings.DATABASE_NAME]
    print("✅ Local MongoDB connected (chat + OCR cache + video links)")
    print("✅ Remote API:", REMOTE_API_BASE)


async def close_db():
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()


# ─────────────────────────────────────────────
# OCR CACHE
# ─────────────────────────────────────────────

async def _get_cached_ocr(assignment_id: str) -> Optional[str]:
    try:
        if database is None:
            return None
        col = database["assignment_ocr_cache"]
        doc = await col.find_one({"assignment_id": assignment_id})
        if doc:
            print(f"✅ OCR Cache HIT for {assignment_id} — skipping OCR")
            return doc["full_text"]
        return None
    except Exception as e:
        print(f"❌ Cache read error: {e}")
        return None


async def _save_ocr_cache(assignment_id: str, full_text: str):
    try:
        if database is None:
            return
        col = database["assignment_ocr_cache"]
        await col.update_one(
            {"assignment_id": assignment_id},
            {"$set": {"assignment_id": assignment_id, "full_text": full_text}},
            upsert=True
        )
        print(f"✅ OCR result cached for {assignment_id}")
    except Exception as e:
        print(f"❌ Cache save error: {e}")


# ─────────────────────────────────────────────
# VIDEO LINKS
# ─────────────────────────────────────────────

async def save_video_links(
    student_id: str,
    assignment_id: str,
    question: str,
    video_links: list
):
    """Video links MongoDB তে save করো"""
    try:
        if database is None:
            return
        col = database["video_links"]
        doc = {
            "student_id": student_id,
            "assignment_id": assignment_id,
            "question": question,
            "video_links": video_links,
            "created_at": datetime.utcnow()
        }
        await col.insert_one(doc)
        print(f"✅ {len(video_links)} video links saved for student {student_id}")
    except Exception as e:
        print(f"❌ Video links save error: {e}")


async def get_video_links(
    student_id: str,
    assignment_id: str
) -> List[dict]:
    """Student এর সব video links আনো"""
    try:
        if database is None:
            return []
        col = database["video_links"]
        cursor = col.find(
            {"student_id": student_id, "assignment_id": assignment_id},
            {"_id": 0}
        ).sort("created_at", -1)
        results = await cursor.to_list(length=50)
        return results
    except Exception as e:
        print(f"❌ Video links fetch error: {e}")
        return []


# ─────────────────────────────────────────────
# HELPER: Download PDF and OCR it
# ─────────────────────────────────────────────

async def _extract_text_from_url(file_url: str) -> str:
    from app.services.ocr_service import extract_text_from_file

    try:
        print(f"📥 Downloading file from: {file_url}")
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(file_url)
            response.raise_for_status()

        ext = os.path.splitext(file_url.split("?")[0])[1].lower() or ".pdf"

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        print(f"✅ File downloaded to temp: {tmp_path}")
        pages = await extract_text_from_file(tmp_path)
        os.unlink(tmp_path)

        full_text = "\n\n".join([p["content"] for p in pages])
        print(f"✅ OCR complete — {len(pages)} pages, {len(full_text)} chars")
        return full_text

    except Exception as e:
        print(f"❌ OCR from URL failed: {e}")
        return ""


# ─────────────────────────────────────────────
# ASSIGNMENT — Remote API
# ─────────────────────────────────────────────

async def save_assignment(assignment_data: dict):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{REMOTE_API_BASE}/assignments",
            json=assignment_data
        )
        response.raise_for_status()
        return response.json()


async def get_all_assignments(teacher_id: Optional[str] = None) -> List[dict]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            params = {"teacher_id": teacher_id} if teacher_id else {}
            response = await client.get(f"{REMOTE_API_BASE}/assignments", params=params)
            response.raise_for_status()
            data = response.json()
            assignments = data.get("assignments", data) if isinstance(data, dict) else data
            return [_normalize(a) for a in assignments]
    except Exception as e:
        print(f"❌ Remote API error (get_all_assignments): {e}")
        return []


async def get_assignment_by_id(assignment_id: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{REMOTE_API_BASE}/assignments/{assignment_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()

        assignment = data.get("data", data)
        _normalize(assignment)

        title        = assignment.get("title", "")
        subject      = (assignment.get("subject") or {}).get("name", "")
        grade        = (assignment.get("grade") or {}).get("name", "")
        instructions = assignment.get("instructions", "")
        score        = assignment.get("score", "")
        due_date     = assignment.get("dueDate", "")
        file_url     = assignment.get("fileUrl", "")

        print(f"\n{'='*60}")
        print(f"📋 Assignment: {title}")
        print(f"   Instructions length: {len(instructions)} chars")
        print(f"   File URL: {file_url}")
        print(f"{'='*60}")

        # Cache check
        pdf_text = await _get_cached_ocr(assignment_id)

        if pdf_text is None:
            print(f"⚠️  OCR Cache MISS — running OCR now...")
            if file_url:
                pdf_text = await _extract_text_from_url(file_url)
                await _save_ocr_cache(assignment_id, pdf_text)
            else:
                pdf_text = ""

        parts = [
            f"Assignment Title: {title}",
            f"Subject: {subject}",
            f"Grade: {grade}",
            f"Total Score: {score}",
            f"Due Date: {due_date}",
            "",
            "=== INSTRUCTIONS ===",
            instructions,
        ]

        if pdf_text:
            parts += [
                "",
                "=== ASSIGNMENT CONTENT (from PDF) ===",
                pdf_text,
            ]

        assignment["full_text"] = "\n".join(parts).strip()
        print(f"✅ full_text ready — {len(assignment['full_text'])} total chars")

        return assignment

    except Exception as e:
        print(f"❌ Remote API error (get_assignment_by_id): {e}")
        return None


async def get_assignment_full_text(assignment_id: str) -> Optional[str]:
    assignment = await get_assignment_by_id(assignment_id)
    if not assignment:
        return None
    return assignment.get("full_text", "")


async def delete_assignment(assignment_id: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.delete(f"{REMOTE_API_BASE}/assignments/{assignment_id}")
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"❌ Remote API error (delete_assignment): {e}")
        return False


async def search_assignments(query: str, teacher_id: Optional[str] = None) -> List[dict]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            params = {"q": query}
            if teacher_id:
                params["teacher_id"] = teacher_id
            response = await client.get(f"{REMOTE_API_BASE}/assignments/search", params=params)
            response.raise_for_status()
            data = response.json()
            assignments = data.get("assignments", data) if isinstance(data, dict) else data
            return [_normalize(a) for a in assignments]
    except Exception as e:
        print(f"❌ Remote API error (search_assignments): {e}")
        return []


async def get_database_stats() -> dict:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{REMOTE_API_BASE}/stats")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"total_assignments": 0, "error": str(e)}