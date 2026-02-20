# import google.generativeai as genai
# from app.config import settings
# from app.services.s3_service import upload_mindmap_to_s3
# import json
# import base64
# import io
# from PIL import Image, ImageDraw, ImageFont
# import math
# import logging

# logger = logging.getLogger(__name__)

# # Configure Gemini API
# api_key = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else settings.OPENAI_API_KEY
# genai.configure(api_key=api_key)


# # =====================================================
# # SMART GEMINI MODEL AUTO-FALLBACK SYSTEM
# # =====================================================

# MODEL_CANDIDATES = [
#     "gemini-2.0-flash-lite",
#     "gemini-2.0-flash",
#     "gemini-2.5-flash",
# ]

# def initialize_model():
#     for model_name in MODEL_CANDIDATES:
#         try:
#             logger.info(f"Trying Gemini model: {model_name}")
#             test_model = genai.GenerativeModel(model_name)
#             test_model.generate_content("Hello")
#             logger.info(f"Using Gemini model: {model_name}")
#             return test_model
#         except Exception as e:
#             logger.warning(f"Model {model_name} failed: {e}")
#             continue
#     raise RuntimeError("No available Gemini model found.")

# model = initialize_model()


# # =====================================================
# # MAIN SERVICE FUNCTIONS
# # =====================================================

# async def generate_mindmap_data(
#     prompt: str,
#     student_id: str = None,
#     format: str = "png",
#     upload_to_s3: bool = True
# ) -> dict:

#     try:
#         mindmap_structure = await get_mindmap_structure(prompt)

#         if format.lower() == "svg":
#             image_data = create_mindmap_svg(mindmap_structure)
#             mime_type = "image/svg+xml"
#         else:
#             image_data = create_mindmap_image(mindmap_structure)
#             mime_type = "image/png"

#         total_nodes = count_nodes(mindmap_structure)
#         image_bytes = base64.b64decode(image_data)

#         result = {
#             "topic": mindmap_structure["topic"],
#             "total_nodes": total_nodes,
#             "format": format,
#         }

#         if upload_to_s3:
#             s3_url = await upload_mindmap_to_s3(
#                 image_bytes=image_bytes,
#                 student_id=student_id,
#                 topic=mindmap_structure["topic"],
#                 format=format
#             )
#             result["s3_url"] = s3_url
#             result["image_url"] = s3_url
#         else:
#             result["image_base64"] = image_data
#             result["image_url"] = f"data:{mime_type};base64,{image_data}"

#         return result

#     except json.JSONDecodeError as e:
#         logger.error(f"Failed to parse Gemini response: {e}")
#         raise ValueError("Invalid mind map structure received")
#     except Exception as e:
#         logger.error(f"Error generating mind map: {e}")
#         raise


# async def get_mindmap_structure(prompt: str) -> dict:

#     system_prompt = """You are a mind map generator. Given a topic, create a hierarchical mind map structure.

# Return ONLY a valid JSON object with this exact structure:
# {
#     "topic": "Main Topic",
#     "branches": [
#         {
#             "name": "Branch 1",
#             "subbranches": ["Sub 1", "Sub 2", "Sub 3"]
#         }
#     ]
# }

# Rules:
# - Maximum 6 main branches
# - Maximum 5 subbranches per branch
# - Keep names concise (2-4 words max)
# - Make it educational and well-organized
# - Ensure JSON is properly formatted
# - Return ONLY JSON, no markdown, no explanations
# """

#     try:
#         message = f"{system_prompt}\n\nCreate a mind map for: {prompt}"

#         response = model.generate_content(
#             message,
#             generation_config=genai.types.GenerationConfig(
#                 temperature=0.7,
#                 max_output_tokens=1500
#             )
#         )

#         content = response.text.strip()

#         if content.startswith("```json"):
#             content = content[7:]
#         elif content.startswith("```"):
#             content = content[3:]

#         if content.endswith("```"):
#             content = content[:-3]

#         content = content.strip()

#         mindmap_structure = json.loads(content)

#         if "topic" not in mindmap_structure or "branches" not in mindmap_structure:
#             raise ValueError("Invalid mind map structure")

#         if not isinstance(mindmap_structure["branches"], list):
#             raise ValueError("Branches must be a list")

#         return mindmap_structure

#     except Exception as e:
#         logger.error(f"Error generating mind map with Gemini: {e}")
#         raise


# # =====================================================
# # UTILITY FUNCTIONS
# # =====================================================

# def count_nodes(structure: dict) -> int:
#     total = 1
#     for branch in structure.get("branches", []):
#         total += 1
#         total += len(branch.get("subbranches", []))
#     return total


# def lighten_hex_color(hex_color: str, factor: float = 0.4) -> str:
#     hex_color = hex_color.lstrip('#')
#     r = int(hex_color[0:2], 16)
#     g = int(hex_color[2:4], 16)
#     b = int(hex_color[4:6], 16)
#     r = min(255, int(r + (255 - r) * factor))
#     g = min(255, int(g + (255 - g) * factor))
#     b = min(255, int(b + (255 - b) * factor))
#     return f'#{r:02x}{g:02x}{b:02x}'


# def escape_xml(text: str) -> str:
#     return (text.replace('&', '&amp;')
#                 .replace('<', '&lt;')
#                 .replace('>', '&gt;')
#                 .replace('"', '&quot;')
#                 .replace("'", '&apos;'))


# def load_font(size: int):
#     font_options = [
#         "arial.ttf",
#         "Arial.ttf",
#         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
#         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
#         "/System/Library/Fonts/Helvetica.ttc",
#         "C:\\Windows\\Fonts\\arial.ttf",
#         "C:\\Windows\\Fonts\\calibri.ttf"
#     ]
#     for font_path in font_options:
#         try:
#             return ImageFont.truetype(font_path, size)
#         except (OSError, IOError):
#             continue
#     logger.warning("Could not load TrueType font, using default")
#     return ImageFont.load_default()


# def draw_text_centered(draw, text, x, y, font, color, max_width=200):
#     words = text.split()
#     lines = []
#     current_line = []

#     for word in words:
#         test_line = ' '.join(current_line + [word])
#         try:
#             bbox = draw.textbbox((0, 0), test_line, font=font)
#             text_width = bbox[2] - bbox[0]
#         except:
#             text_width = len(test_line) * (font.size if hasattr(font, 'size') else 10)

#         if text_width <= max_width:
#             current_line.append(word)
#         else:
#             if current_line:
#                 lines.append(' '.join(current_line))
#             current_line = [word]

#     if current_line:
#         lines.append(' '.join(current_line))

#     line_height = 20
#     total_height = len(lines) * line_height
#     start_y = y - (total_height / 2) + (line_height / 2)

#     for i, line in enumerate(lines):
#         try:
#             bbox = draw.textbbox((0, 0), line, font=font)
#             text_width = bbox[2] - bbox[0]
#         except:
#             text_width = len(line) * (font.size if hasattr(font, 'size') else 10) * 0.6

#         text_x = x - (text_width / 2)
#         text_y = start_y + (i * line_height)
#         draw.text((text_x, text_y), line, fill=color, font=font)


# def create_empty_mindmap(topic: str) -> str:
#     img = Image.new('RGB', (800, 600), color='#F8F9FA')
#     draw = ImageDraw.Draw(img)
#     font = load_font(24)
#     draw_text_centered(draw, topic, 400, 300, font, '#6C5CE7', max_width=300)
#     buffer = io.BytesIO()
#     img.save(buffer, format='PNG')
#     buffer.seek(0)
#     return base64.b64encode(buffer.getvalue()).decode('utf-8')


# # =====================================================
# # IMAGE GENERATION FUNCTIONS
# # =====================================================

# def create_mindmap_image(data: dict) -> str:
#     width = 1400
#     height = 1000
#     center_x = width // 2
#     center_y = height // 2

#     img = Image.new('RGB', (width, height), color='#F8F9FA')
#     draw = ImageDraw.Draw(img)

#     colors = [
#         "#FF6B6B",
#         "#4ECDC4",
#         "#45B7D1",
#         "#FFA07A",
#         "#98D8C8",
#         "#F7DC6F",
#     ]

#     font_title = load_font(24)
#     font_branch = load_font(18)
#     font_sub = load_font(14)

#     branches = data.get('branches', [])
#     num_branches = len(branches)

#     if num_branches == 0:
#         logger.warning("No branches in mind map")
#         return create_empty_mindmap(data.get('topic', 'Mind Map'))

#     # Step 1: Draw connections (lines)
#     for i, branch in enumerate(branches):
#         angle = (2 * math.pi * i / num_branches) - math.pi / 2
#         branch_x = center_x + 300 * math.cos(angle)
#         branch_y = center_y + 300 * math.sin(angle)

#         color = colors[i % len(colors)]

#         draw.line([(center_x, center_y), (branch_x, branch_y)],
#                   fill=color, width=4)

#         subbranches = branch.get('subbranches', [])
#         num_subs = len(subbranches)

#         for j, subbranch in enumerate(subbranches):
#             sub_angle = angle + (j - num_subs / 2 + 0.5) * 0.5
#             sub_x = branch_x + 180 * math.cos(sub_angle)
#             sub_y = branch_y + 180 * math.sin(sub_angle)

#             draw.line([(branch_x, branch_y), (sub_x, sub_y)],
#                       fill=color, width=2)

#     # Step 2: Draw center node
#     topic = data.get('topic', 'Mind Map')

#     shadow_offset = 5
#     draw.ellipse([center_x - 85 + shadow_offset, center_y - 85 + shadow_offset,
#                   center_x + 85 + shadow_offset, center_y + 85 + shadow_offset],
#                  fill='#CCCCCC')

#     draw.ellipse([center_x - 80, center_y - 80, center_x + 80, center_y + 80],
#                  fill='#6C5CE7', outline='white', width=3)

#     draw_text_centered(draw, topic, center_x, center_y, font_title, 'white', max_width=140)

#     # Step 3: Draw branch nodes
#     for i, branch in enumerate(branches):
#         angle = (2 * math.pi * i / num_branches) - math.pi / 2
#         branch_x = center_x + 300 * math.cos(angle)
#         branch_y = center_y + 300 * math.sin(angle)

#         color = colors[i % len(colors)]
#         branch_name = branch.get('name', '')

#         draw.rounded_rectangle([branch_x - 73, branch_y - 33, branch_x + 73, branch_y + 33],
#                                 radius=10, fill='#CCCCCC')

#         draw.rounded_rectangle([branch_x - 70, branch_y - 30, branch_x + 70, branch_y + 30],
#                                 radius=10, fill=color, outline='white', width=2)

#         draw_text_centered(draw, branch_name, branch_x, branch_y, font_branch, 'white', max_width=120)

#         # Step 4: Draw subbranch nodes
#         subbranches = branch.get('subbranches', [])
#         num_subs = len(subbranches)

#         for j, subbranch in enumerate(subbranches):
#             sub_angle = angle + (j - num_subs / 2 + 0.5) * 0.5
#             sub_x = branch_x + 180 * math.cos(sub_angle)
#             sub_y = branch_y + 180 * math.sin(sub_angle)

#             light_color = lighten_hex_color(color)

#             draw.ellipse([sub_x - 63, sub_y - 38, sub_x + 63, sub_y + 38],
#                          fill='#DDDDDD')

#             draw.ellipse([sub_x - 60, sub_y - 35, sub_x + 60, sub_y + 35],
#                          fill=light_color, outline=color, width=2)

#             draw_text_centered(draw, subbranch, sub_x, sub_y, font_sub, '#2C3E50', max_width=100)

#     buffer = io.BytesIO()
#     img.save(buffer, format='PNG', quality=95, optimize=True)
#     buffer.seek(0)
#     image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

#     return image_base64


# def create_mindmap_svg(data: dict) -> str:
#     width = 1400
#     height = 1000
#     center_x = width // 2
#     center_y = height // 2

#     colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", "#F7DC6F"]

#     branches = data.get('branches', [])
#     num_branches = len(branches)
#     topic = data.get('topic', 'Mind Map')

#     svg_parts = [
#         f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
#         '<defs>',
#         '<filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">',
#         '<feGaussianBlur in="SourceAlpha" stdDeviation="3"/>',
#         '<feOffset dx="2" dy="2" result="offsetblur"/>',
#         '<feComponentTransfer><feFuncA type="linear" slope="0.3"/></feComponentTransfer>',
#         '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>',
#         '</filter>',
#         '</defs>',
#         f'<rect width="{width}" height="{height}" fill="#F8F9FA"/>'
#     ]

#     if num_branches == 0:
#         svg_parts.extend([
#             f'<circle cx="{center_x}" cy="{center_y}" r="80" fill="#6C5CE7" stroke="white" stroke-width="3" filter="url(#shadow)"/>',
#             f'<text x="{center_x}" y="{center_y}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="20" font-weight="bold">{escape_xml(topic)}</text>',
#             '</svg>'
#         ])
#     else:
#         # Draw lines
#         for i, branch in enumerate(branches):
#             angle = (2 * math.pi * i / num_branches) - math.pi / 2
#             branch_x = center_x + 300 * math.cos(angle)
#             branch_y = center_y + 300 * math.sin(angle)
#             color = colors[i % len(colors)]

#             svg_parts.append(f'<line x1="{center_x}" y1="{center_y}" x2="{branch_x}" y2="{branch_y}" stroke="{color}" stroke-width="4" opacity="0.6"/>')

#             subbranches = branch.get('subbranches', [])
#             num_subs = len(subbranches)

#             for j, subbranch in enumerate(subbranches):
#                 sub_angle = angle + (j - num_subs / 2 + 0.5) * 0.5
#                 sub_x = branch_x + 180 * math.cos(sub_angle)
#                 sub_y = branch_y + 180 * math.sin(sub_angle)
#                 svg_parts.append(f'<line x1="{branch_x}" y1="{branch_y}" x2="{sub_x}" y2="{sub_y}" stroke="{color}" stroke-width="2" opacity="0.4"/>')

#         # Draw center node
#         svg_parts.extend([
#             '<g filter="url(#shadow)">',
#             f'<circle cx="{center_x}" cy="{center_y}" r="80" fill="#6C5CE7" stroke="white" stroke-width="3"/>',
#             f'<text x="{center_x}" y="{center_y}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="18" font-weight="bold">{escape_xml(topic)}</text>',
#             '</g>'
#         ])

#         # Draw branches and subbranches
#         for i, branch in enumerate(branches):
#             angle = (2 * math.pi * i / num_branches) - math.pi / 2
#             branch_x = center_x + 300 * math.cos(angle)
#             branch_y = center_y + 300 * math.sin(angle)
#             color = colors[i % len(colors)]
#             branch_name = branch.get('name', '')

#             svg_parts.extend([
#                 '<g filter="url(#shadow)">',
#                 f'<rect x="{branch_x - 70}" y="{branch_y - 30}" width="140" height="60" rx="10" fill="{color}" stroke="white" stroke-width="2"/>',
#                 f'<text x="{branch_x}" y="{branch_y}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="14" font-weight="bold">{escape_xml(branch_name)}</text>',
#                 '</g>'
#             ])

#             subbranches = branch.get('subbranches', [])
#             num_subs = len(subbranches)

#             for j, subbranch in enumerate(subbranches):
#                 sub_angle = angle + (j - num_subs / 2 + 0.5) * 0.5
#                 sub_x = branch_x + 180 * math.cos(sub_angle)
#                 sub_y = branch_y + 180 * math.sin(sub_angle)
#                 light_color = lighten_hex_color(color)

#                 svg_parts.extend([
#                     '<g filter="url(#shadow)">',
#                     f'<ellipse cx="{sub_x}" cy="{sub_y}" rx="60" ry="35" fill="{light_color}" stroke="{color}" stroke-width="2"/>',
#                     f'<text x="{sub_x}" y="{sub_y}" text-anchor="middle" dominant-baseline="middle" fill="#2C3E50" font-size="12">{escape_xml(subbranch)}</text>',
#                     '</g>'
#                 ])

#         svg_parts.append('</svg>')

#     svg_content = '\n'.join(svg_parts)
#     return base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')




import google.generativeai as genai
from app.config import settings
import json
import base64
import io
import math
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe
from matplotlib.path import Path
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# =====================================================
# AI PROVIDER SETUP (GEMINI + GPT FALLBACK)
# =====================================================

AI_PROVIDER = None  # "gemini" or "openai"
gemini_model = None
openai_client = None

def initialize_ai():
    global AI_PROVIDER, gemini_model, openai_client

    # Try Gemini first
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    if gemini_key:
        GEMINI_MODELS = [
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.5-flash",
        ]
        genai.configure(api_key=gemini_key)
        for model_name in GEMINI_MODELS:
            try:
                test_model = genai.GenerativeModel(model_name)
                # ✅ Test call করো — 403/429 হলে skip করবে
                test_model.generate_content("Hi")
                gemini_model = test_model
                AI_PROVIDER = "gemini"
                logger.info(f"✅ Using Gemini model: {model_name}")
                return
            except Exception as e:
                logger.warning(f"Gemini model {model_name} failed: {e}")
                continue  # সব model fail করলে OpenAI তে যাবে

    # Fallback to OpenAI
    openai_key = getattr(settings, 'OPENAI_API_KEY', None)
    if openai_key:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_key)
            AI_PROVIDER = "openai"
            logger.info("✅ Using OpenAI GPT as fallback.")
            return
        except Exception as e:
            logger.warning(f"OpenAI init failed: {e}")

    logger.error("❌ No AI provider available.")

initialize_ai()


# =====================================================
# S3 IMPORT (safe)
# =====================================================

try:
    from app.services.s3_service import upload_mindmap_to_s3
except Exception:
    async def upload_mindmap_to_s3(**kwargs):
        raise RuntimeError("S3 service not available")


# =====================================================
# MAIN SERVICE FUNCTIONS
# =====================================================

async def generate_mindmap_data(
    prompt: str,
    student_id: str = None,
    format: str = "png",
    upload_to_s3: bool = True
) -> dict:

    try:
        mindmap_structure = await get_mindmap_structure(prompt)

        if format.lower() == "svg":
            image_data = create_mindmap_svg(mindmap_structure)
            mime_type = "image/svg+xml"
        else:
            image_data = create_mindmap_image(mindmap_structure)
            mime_type = "image/png"

        total_nodes = count_nodes(mindmap_structure)
        image_bytes = base64.b64decode(image_data)

        result = {
            "topic": mindmap_structure["topic"],
            "total_nodes": total_nodes,
            "format": format,
        }

        if upload_to_s3:
            from app.services.s3_service import upload_mindmap_to_s3 as s3_upload
            s3_url = await s3_upload(
                image_bytes=image_bytes,
                student_id=student_id,
                topic=mindmap_structure["topic"],
                format=format
            )
            result["s3_url"] = s3_url
            result["image_url"] = s3_url
        else:
            result["image_base64"] = image_data
            result["image_url"] = f"data:{mime_type};base64,{image_data}"

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        raise ValueError("Invalid mind map structure received")
    except Exception as e:
        logger.error(f"Error generating mind map: {e}")
        raise


async def get_mindmap_structure(prompt: str) -> dict:
    if AI_PROVIDER == "gemini":
        return await _get_structure_gemini(prompt)
    elif AI_PROVIDER == "openai":
        return await _get_structure_openai(prompt)
    else:
        raise RuntimeError("No AI provider available. Please set GEMINI_API_KEY or OPENAI_API_KEY.")


SYSTEM_PROMPT = """You are a mind map generator. Given a topic, create a hierarchical mind map structure.

Return ONLY a valid JSON object with this exact structure:
{
    "topic": "Main Topic",
    "branches": [
        {
            "name": "Branch 1",
            "subbranches": ["Sub 1", "Sub 2", "Sub 3"]
        }
    ]
}

Rules:
- Maximum 6 main branches
- Maximum 5 subbranches per branch
- Keep names concise (2-4 words max)
- Make it educational and well-organized
- Ensure JSON is properly formatted
- Return ONLY JSON, no markdown, no explanations
"""


async def _get_structure_gemini(prompt: str) -> dict:
    try:
        message = f"{SYSTEM_PROMPT}\n\nCreate a mind map for: {prompt}"
        response = gemini_model.generate_content(
            message,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1500
            )
        )
        return _parse_json_response(response.text)
    except Exception as e:
        logger.error(f"Gemini structure generation failed: {e}")
        raise


async def _get_structure_openai(prompt: str) -> dict:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Create a mind map for: {prompt}"}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return _parse_json_response(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"OpenAI structure generation failed: {e}")
        raise


def _parse_json_response(content: str) -> dict:
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    mindmap_structure = json.loads(content)

    if "topic" not in mindmap_structure or "branches" not in mindmap_structure:
        raise ValueError("Invalid mind map structure")
    if not isinstance(mindmap_structure["branches"], list):
        raise ValueError("Branches must be a list")

    return mindmap_structure


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def count_nodes(structure: dict) -> int:
    total = 1
    for branch in structure.get("branches", []):
        total += 1
        total += len(branch.get("subbranches", []))
    return total


def lighten_hex_color(hex_color: str, factor: float = 0.4) -> str:
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f'#{r:02x}{g:02x}{b:02x}'


def escape_xml(text: str) -> str:
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


# =====================================================
# MATPLOTLIB IMAGE GENERATION (BEAUTIFUL)
# =====================================================

COLORS = [
    {"main": "#E74C3C", "light": "#FADBD8", "dark": "#C0392B"},
    {"main": "#2ECC71", "light": "#D5F5E3", "dark": "#27AE60"},
    {"main": "#3498DB", "light": "#D6EAF8", "dark": "#2980B9"},
    {"main": "#F39C12", "light": "#FDEBD0", "dark": "#D68910"},
    {"main": "#9B59B6", "light": "#E8DAEF", "dark": "#7D3C98"},
    {"main": "#1ABC9C", "light": "#D1F2EB", "dark": "#17A589"},
]


def draw_curved_line(ax, x1, y1, x2, y2, color, lw=2.5, alpha=0.7):
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    offset_x = -(y2 - y1) * 0.15
    offset_y = (x2 - x1) * 0.15

    verts = [(x1, y1), (mid_x + offset_x, mid_y + offset_y), (x2, y2)]
    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
    path = Path(verts, codes)
    patch = patches.PathPatch(path, facecolor='none', edgecolor=color,
                               linewidth=lw, alpha=alpha, zorder=1)
    ax.add_patch(patch)


def draw_center_node(ax, topic):
    glow = plt.Circle((0, 0), 0.57, color='#5D6D7E', alpha=0.3, zorder=4)
    ax.add_patch(glow)
    circle = plt.Circle((0, 0), 0.52, color='#2C3E50', zorder=5)
    ax.add_patch(circle)
    inner = plt.Circle((0, 0), 0.48, color='#34495E', zorder=6)
    ax.add_patch(inner)

    words = topic.split()
    if len(words) > 3:
        mid = len(words) // 2
        text = ' '.join(words[:mid]) + '\n' + ' '.join(words[mid:])
        fontsize = 10
    else:
        text = topic
        fontsize = 12

    ax.text(0, 0, text, ha='center', va='center',
            fontsize=fontsize, fontweight='bold', color='white', zorder=7,
            path_effects=[pe.withStroke(linewidth=2, foreground='#1A252F')])


def draw_branch_node(ax, x, y, name, color_set):
    box_w, box_h = 1.3, 0.42

    shadow = FancyBboxPatch(
        (x - box_w / 2 + 0.04, y - box_h / 2 - 0.04), box_w, box_h,
        boxstyle="round,pad=0.05", facecolor='#00000033', edgecolor='none', zorder=4
    )
    ax.add_patch(shadow)

    fancy = FancyBboxPatch(
        (x - box_w / 2, y - box_h / 2), box_w, box_h,
        boxstyle="round,pad=0.05", facecolor=color_set["main"],
        edgecolor=color_set["dark"], linewidth=2, zorder=5
    )
    ax.add_patch(fancy)

    words = name.split()
    if len(words) > 3:
        mid = len(words) // 2
        text = ' '.join(words[:mid]) + '\n' + ' '.join(words[mid:])
        fontsize = 8.5
    else:
        text = name
        fontsize = 9.5

    ax.text(x, y, text, ha='center', va='center',
            fontsize=fontsize, fontweight='bold', color='white', zorder=6)


def draw_sub_node(ax, x, y, name, color_set):
    ellipse = mpatches.Ellipse(
        (x, y), width=1.1, height=0.36,
        facecolor=color_set["light"], edgecolor=color_set["main"],
        linewidth=1.8, zorder=5
    )
    ax.add_patch(ellipse)

    words = name.split()
    if len(words) > 3:
        mid = len(words) // 2
        text = ' '.join(words[:mid]) + '\n' + ' '.join(words[mid:])
        fontsize = 7
    else:
        text = name
        fontsize = 8

    ax.text(x, y, text, ha='center', va='center',
            fontsize=fontsize, color=color_set["dark"], fontweight='bold', zorder=6)


def create_mindmap_image(data: dict) -> str:
    topic = data.get('topic', 'Mind Map')
    branches = data.get('branches', [])
    num_branches = len(branches)

    if num_branches == 0:
        return create_empty_mindmap(topic)

    fig, ax = plt.subplots(1, 1, figsize=(18, 12))
    ax.set_xlim(-6, 6)
    ax.set_ylim(-4.5, 4.5)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor('#F0F4F8')
    ax.set_facecolor('#F0F4F8')

    for gx in range(-5, 6):
        for gy in range(-4, 5):
            ax.plot(gx, gy, 'o', color='#D5E0EC', markersize=2, alpha=0.4, zorder=0)

    branch_radius = 2.8
    sub_radius = 1.7

    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / num_branches) - math.pi / 2
        bx = branch_radius * math.cos(angle)
        by = branch_radius * math.sin(angle)
        color_set = COLORS[i % len(COLORS)]

        draw_curved_line(ax, 0, 0, bx, by, color_set["main"], lw=3, alpha=0.8)
        draw_branch_node(ax, bx, by, branch.get('name', ''), color_set)

        subbranches = branch.get('subbranches', [])
        num_subs = len(subbranches)

        for j, sub in enumerate(subbranches):
            spread = (j - (num_subs - 1) / 2) * 0.45 if num_subs > 1 else 0
            sub_angle = angle + spread
            sx = bx + sub_radius * math.cos(sub_angle)
            sy = by + sub_radius * math.sin(sub_angle)
            sx = max(-5.5, min(5.5, sx))
            sy = max(-4.0, min(4.0, sy))

            draw_curved_line(ax, bx, by, sx, sy, color_set["main"], lw=1.8, alpha=0.6)
            draw_sub_node(ax, sx, sy, sub, color_set)

    draw_center_node(ax, topic)

    fig.text(0.5, 0.97, topic, ha='center', va='top',
             fontsize=16, fontweight='bold', color='#2C3E50',
             path_effects=[pe.withStroke(linewidth=3, foreground='white')])

    plt.tight_layout(pad=0.5)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='PNG', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def create_empty_mindmap(topic: str) -> str:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis('off')
    fig.patch.set_facecolor('#F0F4F8')
    circle = plt.Circle((0.5, 0.5), 0.2, color='#2C3E50', transform=ax.transAxes)
    ax.add_patch(circle)
    ax.text(0.5, 0.5, topic, ha='center', va='center',
            fontsize=16, fontweight='bold', color='white', transform=ax.transAxes)
    buffer = io.BytesIO()
    plt.savefig(buffer, format='PNG', dpi=120, bbox_inches='tight')
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


# =====================================================
# SVG GENERATION
# =====================================================

def load_font(size: int):
    font_options = [
        "arial.ttf", "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\calibri.ttf"
    ]
    for font_path in font_options:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def create_mindmap_svg(data: dict) -> str:
    width = 1400
    height = 1000
    center_x = width // 2
    center_y = height // 2

    colors = ["#E74C3C", "#2ECC71", "#3498DB", "#F39C12", "#9B59B6", "#1ABC9C"]
    light_colors = ["#FADBD8", "#D5F5E3", "#D6EAF8", "#FDEBD0", "#E8DAEF", "#D1F2EB"]

    branches = data.get('branches', [])
    num_branches = len(branches)
    topic = data.get('topic', 'Mind Map')

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '<filter id="shadow"><feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.2"/></filter>',
        '<radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">',
        '<stop offset="0%" style="stop-color:#F8FBFF"/>',
        '<stop offset="100%" style="stop-color:#E8F0F8"/>',
        '</radialGradient>',
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="url(#bgGrad)"/>'
    ]

    if num_branches == 0:
        svg_parts.extend([
            f'<circle cx="{center_x}" cy="{center_y}" r="80" fill="#2C3E50" filter="url(#shadow)"/>',
            f'<text x="{center_x}" y="{center_y}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="20" font-weight="bold" font-family="Arial">{escape_xml(topic)}</text>',
            '</svg>'
        ])
        return base64.b64encode('\n'.join(svg_parts).encode('utf-8')).decode('utf-8')

    branch_r = 300
    sub_r = 180

    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / num_branches) - math.pi / 2
        bx = center_x + branch_r * math.cos(angle)
        by = center_y + branch_r * math.sin(angle)
        color = colors[i % len(colors)]

        svg_parts.append(
            f'<line x1="{center_x}" y1="{center_y}" x2="{bx:.1f}" y2="{by:.1f}" '
            f'stroke="{color}" stroke-width="4" stroke-linecap="round" opacity="0.7"/>'
        )

        subbranches = branch.get('subbranches', [])
        num_subs = len(subbranches)
        for j, sub in enumerate(subbranches):
            spread = (j - (num_subs - 1) / 2) * 0.45 if num_subs > 1 else 0
            sub_angle = angle + spread
            sx = bx + sub_r * math.cos(sub_angle)
            sy = by + sub_r * math.sin(sub_angle)
            svg_parts.append(
                f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{sx:.1f}" y2="{sy:.1f}" '
                f'stroke="{color}" stroke-width="2" stroke-linecap="round" opacity="0.5"/>'
            )

    svg_parts.extend([
        f'<circle cx="{center_x}" cy="{center_y}" r="75" fill="#2C3E50" filter="url(#shadow)"/>',
        f'<circle cx="{center_x}" cy="{center_y}" r="70" fill="#34495E"/>',
        f'<text x="{center_x}" y="{center_y}" text-anchor="middle" dominant-baseline="middle" '
        f'fill="white" font-size="16" font-weight="bold" font-family="Arial">{escape_xml(topic)}</text>',
    ])

    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / num_branches) - math.pi / 2
        bx = center_x + branch_r * math.cos(angle)
        by = center_y + branch_r * math.sin(angle)
        color = colors[i % len(colors)]
        light = light_colors[i % len(light_colors)]
        branch_name = escape_xml(branch.get('name', ''))

        svg_parts.extend([
            f'<rect x="{bx - 70:.1f}" y="{by - 28:.1f}" width="140" height="56" rx="12" '
            f'fill="{color}" filter="url(#shadow)"/>',
            f'<text x="{bx:.1f}" y="{by:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'fill="white" font-size="13" font-weight="bold" font-family="Arial">{branch_name}</text>',
        ])

        subbranches = branch.get('subbranches', [])
        num_subs = len(subbranches)
        for j, sub in enumerate(subbranches):
            spread = (j - (num_subs - 1) / 2) * 0.45 if num_subs > 1 else 0
            sub_angle = angle + spread
            sx = bx + sub_r * math.cos(sub_angle)
            sy = by + sub_r * math.sin(sub_angle)
            sub_name = escape_xml(sub)

            svg_parts.extend([
                f'<ellipse cx="{sx:.1f}" cy="{sy:.1f}" rx="62" ry="28" '
                f'fill="{light}" stroke="{color}" stroke-width="2" filter="url(#shadow)"/>',
                f'<text x="{sx:.1f}" y="{sy:.1f}" text-anchor="middle" dominant-baseline="middle" '
                f'fill="#2C3E50" font-size="11" font-family="Arial">{sub_name}</text>',
            ])

    svg_parts.append('</svg>')
    return base64.b64encode('\n'.join(svg_parts).encode('utf-8')).decode('utf-8')