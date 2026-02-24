# import google.generativeai as genai
# from app.config import settings
# import json
# import base64
# import random
# import logging
# import httpx
# import os

# logger = logging.getLogger(__name__)

# AI_PROVIDER = None
# gemini_model = None
# openai_client = None


# def initialize_ai():
#     global AI_PROVIDER, gemini_model, openai_client
#     gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
#     if gemini_key:
#         genai.configure(api_key=gemini_key, transport='rest')
#         gemini_model = genai.GenerativeModel("gemini-2.0-flash")
#         AI_PROVIDER = "gemini"
#         logger.info("Using Gemini: gemini-2.0-flash REST")
#         return
#     openai_key = getattr(settings, 'OPENAI_API_KEY', None)
#     if openai_key:
#         try:
#             from openai import OpenAI
#             openai_client = OpenAI(api_key=openai_key)
#             AI_PROVIDER = "openai"
#             logger.info("Using OpenAI GPT fallback")
#             return
#         except Exception as e:
#             logger.warning(f"OpenAI init failed: {e}")
#     logger.error("No AI provider available")


# initialize_ai()


# SYSTEM_PROMPT = """You are a mind map generator. Return ONLY a valid JSON object, no markdown, no code blocks.

# Format:
# {
#     "topic": "Main Topic",
#     "branches": [
#         {
#             "name": "Branch Name",
#             "subbranches": ["Sub 1", "Sub 2", "Sub 3"]
#         }
#     ]
# }

# Rules:
# - Exactly 5 to 6 main branches
# - Exactly 3 to 4 subbranches per branch
# - Names max 4 words each
# - Return ONLY raw JSON"""


# # ─────────────────────────────────────────────
# # FAL IMAGE GENERATION
# # ─────────────────────────────────────────────

# def _build_mindmap_prompt(structure: dict) -> str:
#     """
#     Mindmap structure থেকে ideogram এর জন্য detailed prompt বানাও
#     """
#     topic = structure.get("topic", "Mind Map")
#     branches = structure.get("branches", [])

#     branch_lines = []
#     for branch in branches:
#         name = branch.get("name", "")
#         subs = branch.get("subbranches", [])
#         subs_str = ", ".join(subs)
#         branch_lines.append(f"- {name}: {subs_str}")

#     branches_text = "\n".join(branch_lines)

#     prompt = f"""A clean, professional mind map diagram with the following structure:

# Central topic: "{topic}"

# Main branches and subtopics:
# {branches_text}

# Design requirements:
# - Clear hierarchical mind map layout with center node
# - Central topic "{topic}" in the middle with a prominent colored circle
# - Each main branch radiating outward with colored boxes
# - Subtopics connected to their branches with lines
# - Use vibrant colors for each branch (blue, green, red, purple, orange, teal)
# - Clean white or light background
# - Clear readable fonts, all text clearly visible
# - Professional diagram style
# - Connected nodes with curved lines
# - Balanced layout with branches spread around the center
# - No decorative elements, pure mind map diagram"""

#     return prompt


# async def _generate_image_with_fal(prompt: str) -> str:
#     """
#     FAL ideogram API দিয়ে image generate করো, base64 return করো
#     """
#     fal_key = getattr(settings, 'FAL_KEY', None)
#     if not fal_key:
#         raise RuntimeError("FAL_KEY not configured in settings")

#     url = "https://fal.run/fal-ai/ideogram/v2"

#     payload = {
#         "prompt": prompt,
#         "aspect_ratio": "16:9",
#         "style": "auto",
#         "expand_prompt": False,
#     }

#     headers = {
#         "Authorization": f"Key {fal_key}",
#         "Content-Type": "application/json",
#     }

#     logger.info("📤 Sending request to FAL ideogram...")

#     async with httpx.AsyncClient(timeout=120) as client:
#         response = await client.post(url, json=payload, headers=headers)
#         response.raise_for_status()
#         data = response.json()

#     # FAL response এ image URL থাকে
#     images = data.get("images", [])
#     if not images:
#         raise ValueError("FAL returned no images")

#     image_url = images[0].get("url")
#     if not image_url:
#         raise ValueError("FAL image URL is missing")

#     logger.info(f"✅ FAL image generated: {image_url}")

#     # Image URL থেকে download করে base64 বানাও
#     async with httpx.AsyncClient(timeout=60) as client:
#         img_response = await client.get(image_url)
#         img_response.raise_for_status()
#         image_bytes = img_response.content

#     image_base64 = base64.b64encode(image_bytes).decode("utf-8")
#     logger.info(f"✅ Image converted to base64 ({len(image_base64)} chars)")

#     return image_base64


# # ─────────────────────────────────────────────
# # MAIN ENTRY
# # ─────────────────────────────────────────────

# async def generate_mindmap_data(
#     prompt: str,
#     student_id: str = None,
#     format: str = "png",
# ) -> dict:
#     try:
#         # Step 1: AI দিয়ে mindmap structure বানাও
#         logger.info(f"🧠 Generating mindmap structure for: {prompt}")
#         mindmap_structure = await get_mindmap_structure(prompt)

#         # Step 2: Structure থেকে image prompt বানাও
#         image_prompt = _build_mindmap_prompt(mindmap_structure)
#         logger.info(f"📝 Image prompt built ({len(image_prompt)} chars)")

#         # Step 3: FAL ideogram দিয়ে image generate করো
#         logger.info("🎨 Generating image with FAL ideogram...")
#         image_base64 = await _generate_image_with_fal(image_prompt)

#         total_nodes = count_nodes(mindmap_structure)

#         # Step 4: MongoDB তে save করো
#         mongo_id = await save_mindmap_to_mongo(
#             student_id=student_id,
#             prompt=prompt,
#             topic=mindmap_structure["topic"],
#             image_base64=image_base64,
#             total_nodes=total_nodes,
#             theme="ideogram",
#         )

#         return {
#             "topic": mindmap_structure["topic"],
#             "total_nodes": total_nodes,
#             "format": format,
#             "theme": "ideogram",
#             "mongo_id": mongo_id,
#             "image_base64": image_base64,
#             "image_url": f"data:image/png;base64,{image_base64}",
#         }

#     except json.JSONDecodeError as e:
#         logger.error(f"Failed to parse AI response: {e}")
#         raise ValueError("Invalid mind map structure received")
#     except Exception as e:
#         logger.error(f"Error generating mind map: {e}")
#         raise


# # ─────────────────────────────────────────────
# # MONGODB SAVE
# # ─────────────────────────────────────────────

# async def save_mindmap_to_mongo(
#     student_id: str,
#     prompt: str,
#     topic: str,
#     image_base64: str,
#     total_nodes: int,
#     theme: str,
# ) -> str:
#     try:
#         from app.database import database as db
#         from datetime import datetime

#         doc = {
#             "student_id": student_id,
#             "prompt": prompt,
#             "topic": topic,
#             "image_base64": image_base64,
#             "total_nodes": total_nodes,
#             "theme": theme,
#             "created_at": datetime.utcnow(),
#         }
#         result = await db["mindmaps"].insert_one(doc)
#         logger.info(f"✅ Saved mindmap to MongoDB: {result.inserted_id}")
#         return str(result.inserted_id)
#     except Exception as e:
#         logger.warning(f"MongoDB save failed (non-critical): {e}")
#         return "not_saved"


# # ─────────────────────────────────────────────
# # AI STRUCTURE GENERATION
# # ─────────────────────────────────────────────

# async def get_mindmap_structure(prompt: str) -> dict:
#     if AI_PROVIDER == "gemini":
#         return await _get_structure_gemini(prompt)
#     elif AI_PROVIDER == "openai":
#         return await _get_structure_openai(prompt)
#     else:
#         raise RuntimeError("No AI provider available.")


# async def _get_structure_gemini(prompt: str) -> dict:
#     try:
#         message = f"{SYSTEM_PROMPT}\n\nCreate a mind map for: {prompt}"
#         response = gemini_model.generate_content(
#             message,
#             generation_config=genai.types.GenerationConfig(
#                 temperature=0.7,
#                 max_output_tokens=1500
#             )
#         )
#         return _parse_json_response(response.text)
#     except Exception as e:
#         logger.error(f"Gemini failed: {e}")
#         raise


# async def _get_structure_openai(prompt: str) -> dict:
#     try:
#         response = openai_client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user", "content": f"Create a mind map for: {prompt}"}
#             ],
#             temperature=0.7,
#             max_tokens=1500
#         )
#         return _parse_json_response(response.choices[0].message.content)
#     except Exception as e:
#         logger.error(f"OpenAI failed: {e}")
#         raise


# def _parse_json_response(content: str) -> dict:
#     content = content.strip()
#     if content.startswith("```"):
#         content = content.split("```")[1]
#         if content.startswith("json"):
#             content = content[4:]
#     content = content.strip()
#     data = json.loads(content)
#     if "topic" not in data or "branches" not in data:
#         raise ValueError("Invalid mind map structure")
#     if not isinstance(data["branches"], list):
#         raise ValueError("Branches must be a list")
#     return data


# def count_nodes(structure: dict) -> int:
#     total = 1
#     for branch in structure.get("branches", []):
#         total += 1
#         total += len(branch.get("subbranches", []))
#     return total







import google.generativeai as genai
from app.config import settings
import json
import base64
import random
import logging
import httpx
import os

logger = logging.getLogger(__name__)

AI_PROVIDER = None
gemini_model = None
openai_client = None


# ─────────────────────────────────────────────
# AI INITIALIZATION (FORCE OPENAI)
# ─────────────────────────────────────────────

def initialize_ai():
    global AI_PROVIDER, gemini_model, openai_client

    # Gemini block রাখা হলো কিন্তু ব্যবহার করবো না
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    if gemini_key:
        logger.info("Gemini key detected but OpenAI will be used instead.")

    # ✅ FORCE OPENAI
    openai_key = getattr(settings, 'OPENAI_API_KEY', None)
    if openai_key:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_key)
            AI_PROVIDER = "openai"
            logger.info("Using OpenAI GPT (Forced)")
            return
        except Exception as e:
            logger.warning(f"OpenAI init failed: {e}")

    logger.error("No AI provider available")


initialize_ai()


SYSTEM_PROMPT = """You are a mind map generator. Return ONLY a valid JSON object, no markdown, no code blocks.

Format:
{
    "topic": "Main Topic",
    "branches": [
        {
            "name": "Branch Name",
            "subbranches": ["Sub 1", "Sub 2", "Sub 3"]
        }
    ]
}

Rules:
- Exactly 5 to 6 main branches
- Exactly 3 to 4 subbranches per branch
- Names max 4 words each
- Return ONLY raw JSON"""


# ─────────────────────────────────────────────
# FAL IMAGE GENERATION
# ─────────────────────────────────────────────

def _build_mindmap_prompt(structure: dict) -> str:
    topic = structure.get("topic", "Mind Map")
    branches = structure.get("branches", [])

    branch_lines = []
    for branch in branches:
        name = branch.get("name", "")
        subs = branch.get("subbranches", [])
        subs_str = ", ".join(subs)
        branch_lines.append(f"- {name}: {subs_str}")

    branches_text = "\n".join(branch_lines)

    prompt = f"""A clean, professional mind map diagram with the following structure:

Central topic: "{topic}"

Main branches and subtopics:
{branches_text}

Design requirements:
- Clear hierarchical mind map layout with center node
- Central topic "{topic}" in the middle with a prominent colored circle
- Each main branch radiating outward with colored boxes
- Subtopics connected to their branches with lines
- Use vibrant colors for each branch
- Clean white background
- Clear readable fonts
- Professional diagram style
- Balanced layout
- No decorative elements"""

    return prompt


async def _generate_image_with_fal(prompt: str) -> str:
    fal_key = getattr(settings, 'FAL_KEY', None)
    if not fal_key:
        raise RuntimeError("FAL_KEY not configured in settings")

    url = "https://fal.run/fal-ai/ideogram/v2"

    payload = {
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "style": "auto",
        "expand_prompt": False,
    }

    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json",
    }

    logger.info("📤 Sending request to FAL ideogram...")

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    images = data.get("images", [])
    if not images:
        raise ValueError("FAL returned no images")

    image_url = images[0].get("url")
    if not image_url:
        raise ValueError("FAL image URL is missing")

    logger.info(f"✅ FAL image generated: {image_url}")

    # ✅ FIX: DO NOT convert to base64 for API response
    return image_url


# ─────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────

async def generate_mindmap_data(
    prompt: str,
    student_id: str = None,
    format: str = "png",
) -> dict:
    try:
        logger.info(f"🧠 Generating mindmap structure for: {prompt}")
        mindmap_structure = await get_mindmap_structure(prompt)

        image_prompt = _build_mindmap_prompt(mindmap_structure)
        logger.info(f"📝 Image prompt built")

        logger.info("🎨 Generating image with FAL ideogram...")
        image_url = await _generate_image_with_fal(image_prompt)

        total_nodes = count_nodes(mindmap_structure)

        mongo_id = await save_mindmap_to_mongo(
            student_id=student_id,
            prompt=prompt,
            topic=mindmap_structure["topic"],
            image_url=image_url,  # ✅ changed
            total_nodes=total_nodes,
            theme="ideogram",
        )

        return {
            "topic": mindmap_structure["topic"],
            "total_nodes": total_nodes,
            "format": format,
            "theme": "ideogram",
            "mongo_id": mongo_id,
            "image_url": image_url,   # ✅ no base64
        }

    except Exception as e:
        logger.error(f"Error generating mind map: {e}")
        raise


# ─────────────────────────────────────────────
# MONGODB SAVE
# ─────────────────────────────────────────────

async def save_mindmap_to_mongo(
    student_id: str,
    prompt: str,
    topic: str,
    image_url: str,  # ✅ changed
    total_nodes: int,
    theme: str,
) -> str:
    try:
        from app.database import database as db
        from datetime import datetime

        doc = {
            "student_id": student_id,
            "prompt": prompt,
            "topic": topic,
            "image_url": image_url,   # ✅ no base64 stored
            "total_nodes": total_nodes,
            "theme": theme,
            "created_at": datetime.utcnow(),
        }

        result = await db["mindmaps"].insert_one(doc)
        logger.info(f"✅ Saved mindmap to MongoDB: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.warning(f"MongoDB save failed: {e}")
        return "not_saved"


# ─────────────────────────────────────────────
# OPENAI STRUCTURE GENERATION
# ─────────────────────────────────────────────

async def get_mindmap_structure(prompt: str) -> dict:
    if AI_PROVIDER == "openai":
        return await _get_structure_openai(prompt)
    else:
        raise RuntimeError("OpenAI not configured.")


async def _get_structure_openai(prompt: str) -> dict:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},  # ✅ prevents markdown
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Create a mind map for: {prompt}"}
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        logger.error(f"OpenAI failed: {e}")
        raise


def count_nodes(structure: dict) -> int:
    total = 1
    for branch in structure.get("branches", []):
        total += 1
        total += len(branch.get("subbranches", []))
    return total




