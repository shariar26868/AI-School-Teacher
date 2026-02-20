import google.generativeai as genai
from app.config import settings
from app.services.s3_service import upload_mindmap_to_s3
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import math
import logging

logger = logging.getLogger(__name__)

# Configure Gemini API
api_key = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else settings.OPENAI_API_KEY
genai.configure(api_key=api_key)


# =====================================================
# SMART GEMINI MODEL AUTO-FALLBACK SYSTEM
# =====================================================

MODEL_CANDIDATES = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
]

def initialize_model():
    for model_name in MODEL_CANDIDATES:
        try:
            logger.info(f"Trying Gemini model: {model_name}")
            test_model = genai.GenerativeModel(model_name)
            test_model.generate_content("Hello")
            logger.info(f"Using Gemini model: {model_name}")
            return test_model
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}")
            continue
    raise RuntimeError("No available Gemini model found.")

model = initialize_model()


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
            s3_url = await upload_mindmap_to_s3(
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
        logger.error(f"Failed to parse Gemini response: {e}")
        raise ValueError("Invalid mind map structure received")
    except Exception as e:
        logger.error(f"Error generating mind map: {e}")
        raise


async def get_mindmap_structure(prompt: str) -> dict:

    system_prompt = """You are a mind map generator. Given a topic, create a hierarchical mind map structure.

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

    try:
        message = f"{system_prompt}\n\nCreate a mind map for: {prompt}"

        response = model.generate_content(
            message,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1500
            )
        )

        content = response.text.strip()

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

    except Exception as e:
        logger.error(f"Error generating mind map with Gemini: {e}")
        raise


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


def load_font(size: int):
    font_options = [
        "arial.ttf",
        "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\calibri.ttf"
    ]
    for font_path in font_options:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue
    logger.warning("Could not load TrueType font, using default")
    return ImageFont.load_default()


def draw_text_centered(draw, text, x, y, font, color, max_width=200):
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        try:
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(test_line) * (font.size if hasattr(font, 'size') else 10)

        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    line_height = 20
    total_height = len(lines) * line_height
    start_y = y - (total_height / 2) + (line_height / 2)

    for i, line in enumerate(lines):
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(line) * (font.size if hasattr(font, 'size') else 10) * 0.6

        text_x = x - (text_width / 2)
        text_y = start_y + (i * line_height)
        draw.text((text_x, text_y), line, fill=color, font=font)


def create_empty_mindmap(topic: str) -> str:
    img = Image.new('RGB', (800, 600), color='#F8F9FA')
    draw = ImageDraw.Draw(img)
    font = load_font(24)
    draw_text_centered(draw, topic, 400, 300, font, '#6C5CE7', max_width=300)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


# =====================================================
# IMAGE GENERATION FUNCTIONS
# =====================================================

def create_mindmap_image(data: dict) -> str:
    width = 1400
    height = 1000
    center_x = width // 2
    center_y = height // 2

    img = Image.new('RGB', (width, height), color='#F8F9FA')
    draw = ImageDraw.Draw(img)

    colors = [
        "#FF6B6B",
        "#4ECDC4",
        "#45B7D1",
        "#FFA07A",
        "#98D8C8",
        "#F7DC6F",
    ]

    font_title = load_font(24)
    font_branch = load_font(18)
    font_sub = load_font(14)

    branches = data.get('branches', [])
    num_branches = len(branches)

    if num_branches == 0:
        logger.warning("No branches in mind map")
        return create_empty_mindmap(data.get('topic', 'Mind Map'))

    # Step 1: Draw connections (lines)
    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / num_branches) - math.pi / 2
        branch_x = center_x + 300 * math.cos(angle)
        branch_y = center_y + 300 * math.sin(angle)

        color = colors[i % len(colors)]

        draw.line([(center_x, center_y), (branch_x, branch_y)],
                  fill=color, width=4)

        subbranches = branch.get('subbranches', [])
        num_subs = len(subbranches)

        for j, subbranch in enumerate(subbranches):
            sub_angle = angle + (j - num_subs / 2 + 0.5) * 0.5
            sub_x = branch_x + 180 * math.cos(sub_angle)
            sub_y = branch_y + 180 * math.sin(sub_angle)

            draw.line([(branch_x, branch_y), (sub_x, sub_y)],
                      fill=color, width=2)

    # Step 2: Draw center node
    topic = data.get('topic', 'Mind Map')

    shadow_offset = 5
    draw.ellipse([center_x - 85 + shadow_offset, center_y - 85 + shadow_offset,
                  center_x + 85 + shadow_offset, center_y + 85 + shadow_offset],
                 fill='#CCCCCC')

    draw.ellipse([center_x - 80, center_y - 80, center_x + 80, center_y + 80],
                 fill='#6C5CE7', outline='white', width=3)

    draw_text_centered(draw, topic, center_x, center_y, font_title, 'white', max_width=140)

    # Step 3: Draw branch nodes
    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / num_branches) - math.pi / 2
        branch_x = center_x + 300 * math.cos(angle)
        branch_y = center_y + 300 * math.sin(angle)

        color = colors[i % len(colors)]
        branch_name = branch.get('name', '')

        draw.rounded_rectangle([branch_x - 73, branch_y - 33, branch_x + 73, branch_y + 33],
                                radius=10, fill='#CCCCCC')

        draw.rounded_rectangle([branch_x - 70, branch_y - 30, branch_x + 70, branch_y + 30],
                                radius=10, fill=color, outline='white', width=2)

        draw_text_centered(draw, branch_name, branch_x, branch_y, font_branch, 'white', max_width=120)

        # Step 4: Draw subbranch nodes
        subbranches = branch.get('subbranches', [])
        num_subs = len(subbranches)

        for j, subbranch in enumerate(subbranches):
            sub_angle = angle + (j - num_subs / 2 + 0.5) * 0.5
            sub_x = branch_x + 180 * math.cos(sub_angle)
            sub_y = branch_y + 180 * math.sin(sub_angle)

            light_color = lighten_hex_color(color)

            draw.ellipse([sub_x - 63, sub_y - 38, sub_x + 63, sub_y + 38],
                         fill='#DDDDDD')

            draw.ellipse([sub_x - 60, sub_y - 35, sub_x + 60, sub_y + 35],
                         fill=light_color, outline=color, width=2)

            draw_text_centered(draw, subbranch, sub_x, sub_y, font_sub, '#2C3E50', max_width=100)

    buffer = io.BytesIO()
    img.save(buffer, format='PNG', quality=95, optimize=True)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return image_base64


def create_mindmap_svg(data: dict) -> str:
    width = 1400
    height = 1000
    center_x = width // 2
    center_y = height // 2

    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", "#F7DC6F"]

    branches = data.get('branches', [])
    num_branches = len(branches)
    topic = data.get('topic', 'Mind Map')

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '<filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">',
        '<feGaussianBlur in="SourceAlpha" stdDeviation="3"/>',
        '<feOffset dx="2" dy="2" result="offsetblur"/>',
        '<feComponentTransfer><feFuncA type="linear" slope="0.3"/></feComponentTransfer>',
        '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>',
        '</filter>',
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="#F8F9FA"/>'
    ]

    if num_branches == 0:
        svg_parts.extend([
            f'<circle cx="{center_x}" cy="{center_y}" r="80" fill="#6C5CE7" stroke="white" stroke-width="3" filter="url(#shadow)"/>',
            f'<text x="{center_x}" y="{center_y}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="20" font-weight="bold">{escape_xml(topic)}</text>',
            '</svg>'
        ])
    else:
        # Draw lines
        for i, branch in enumerate(branches):
            angle = (2 * math.pi * i / num_branches) - math.pi / 2
            branch_x = center_x + 300 * math.cos(angle)
            branch_y = center_y + 300 * math.sin(angle)
            color = colors[i % len(colors)]

            svg_parts.append(f'<line x1="{center_x}" y1="{center_y}" x2="{branch_x}" y2="{branch_y}" stroke="{color}" stroke-width="4" opacity="0.6"/>')

            subbranches = branch.get('subbranches', [])
            num_subs = len(subbranches)

            for j, subbranch in enumerate(subbranches):
                sub_angle = angle + (j - num_subs / 2 + 0.5) * 0.5
                sub_x = branch_x + 180 * math.cos(sub_angle)
                sub_y = branch_y + 180 * math.sin(sub_angle)
                svg_parts.append(f'<line x1="{branch_x}" y1="{branch_y}" x2="{sub_x}" y2="{sub_y}" stroke="{color}" stroke-width="2" opacity="0.4"/>')

        # Draw center node
        svg_parts.extend([
            '<g filter="url(#shadow)">',
            f'<circle cx="{center_x}" cy="{center_y}" r="80" fill="#6C5CE7" stroke="white" stroke-width="3"/>',
            f'<text x="{center_x}" y="{center_y}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="18" font-weight="bold">{escape_xml(topic)}</text>',
            '</g>'
        ])

        # Draw branches and subbranches
        for i, branch in enumerate(branches):
            angle = (2 * math.pi * i / num_branches) - math.pi / 2
            branch_x = center_x + 300 * math.cos(angle)
            branch_y = center_y + 300 * math.sin(angle)
            color = colors[i % len(colors)]
            branch_name = branch.get('name', '')

            svg_parts.extend([
                '<g filter="url(#shadow)">',
                f'<rect x="{branch_x - 70}" y="{branch_y - 30}" width="140" height="60" rx="10" fill="{color}" stroke="white" stroke-width="2"/>',
                f'<text x="{branch_x}" y="{branch_y}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="14" font-weight="bold">{escape_xml(branch_name)}</text>',
                '</g>'
            ])

            subbranches = branch.get('subbranches', [])
            num_subs = len(subbranches)

            for j, subbranch in enumerate(subbranches):
                sub_angle = angle + (j - num_subs / 2 + 0.5) * 0.5
                sub_x = branch_x + 180 * math.cos(sub_angle)
                sub_y = branch_y + 180 * math.sin(sub_angle)
                light_color = lighten_hex_color(color)

                svg_parts.extend([
                    '<g filter="url(#shadow)">',
                    f'<ellipse cx="{sub_x}" cy="{sub_y}" rx="60" ry="35" fill="{light_color}" stroke="{color}" stroke-width="2"/>',
                    f'<text x="{sub_x}" y="{sub_y}" text-anchor="middle" dominant-baseline="middle" fill="#2C3E50" font-size="12">{escape_xml(subbranch)}</text>',
                    '</g>'
                ])

        svg_parts.append('</svg>')

    svg_content = '\n'.join(svg_parts)
    return base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')