# import google.generativeai as genai
# from app.config import settings
# import json
# import base64
# import io
# import math
# import random
# import logging
# import matplotlib
# matplotlib.use('Agg')
# import matplotlib.pyplot as plt
# import matplotlib.patches as mpatches
# from matplotlib.patches import FancyBboxPatch
# import matplotlib.patheffects as pe
# from matplotlib.path import Path
# import matplotlib.patches as patches

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

# try:
#     from app.services.s3_service import upload_mindmap_to_s3
# except Exception:
#     async def upload_mindmap_to_s3(**kwargs):
#         raise RuntimeError("S3 not available")


# THEMES = [
#     {
#         "name": "Corporate",
#         "bg": "#FFFFFF", "fig_bg": "#F8F9FA",
#         "center_bg": "#1A1A2E", "center_text": "white",
#         "branch_colors": [
#             {"box": "#2563EB", "text": "white", "sub_face": "#EFF6FF", "sub_edge": "#2563EB", "sub_text": "#1E3A8A"},
#             {"box": "#16A34A", "text": "white", "sub_face": "#F0FDF4", "sub_edge": "#16A34A", "sub_text": "#14532D"},
#             {"box": "#DC2626", "text": "white", "sub_face": "#FEF2F2", "sub_edge": "#DC2626", "sub_text": "#7F1D1D"},
#             {"box": "#7C3AED", "text": "white", "sub_face": "#F5F3FF", "sub_edge": "#7C3AED", "sub_text": "#4C1D95"},
#             {"box": "#0891B2", "text": "white", "sub_face": "#ECFEFF", "sub_edge": "#0891B2", "sub_text": "#164E63"},
#             {"box": "#EA580C", "text": "white", "sub_face": "#FFF7ED", "sub_edge": "#EA580C", "sub_text": "#7C2D12"},
#         ],
#         "line_alpha": 0.7, "sub_shape": "rounded_rect",
#     },
#     {
#         "name": "Pastel",
#         "bg": "#FDF6EC", "fig_bg": "#FDF6EC",
#         "center_bg": "#4A4A4A", "center_text": "white",
#         "branch_colors": [
#             {"box": "#F4A261", "text": "white", "sub_face": "#FFF8F0", "sub_edge": "#F4A261", "sub_text": "#7B3F00"},
#             {"box": "#E76F51", "text": "white", "sub_face": "#FFF5F2", "sub_edge": "#E76F51", "sub_text": "#7F1D1D"},
#             {"box": "#2A9D8F", "text": "white", "sub_face": "#F0FAFA", "sub_edge": "#2A9D8F", "sub_text": "#134E4A"},
#             {"box": "#264653", "text": "white", "sub_face": "#EEF4F8", "sub_edge": "#264653", "sub_text": "#1E3A5F"},
#             {"box": "#E9C46A", "text": "#3A2800", "sub_face": "#FFFBEA", "sub_edge": "#E9C46A", "sub_text": "#5C4000"},
#             {"box": "#A8DADC", "text": "#1A3A3C", "sub_face": "#F0FBFC", "sub_edge": "#A8DADC", "sub_text": "#1A4A4C"},
#         ],
#         "line_alpha": 0.6, "sub_shape": "ellipse",
#     },
#     {
#         "name": "Dark Neon",
#         "bg": "#0D0D1A", "fig_bg": "#0D0D1A",
#         "center_bg": "#1A1A2E", "center_text": "#E9D5FF",
#         "branch_colors": [
#             {"box": "#7C3AED", "text": "white", "sub_face": "#13102A", "sub_edge": "#A78BFA", "sub_text": "#C4B5FD"},
#             {"box": "#0EA5E9", "text": "white", "sub_face": "#07192E", "sub_edge": "#38BDF8", "sub_text": "#7DD3FC"},
#             {"box": "#10B981", "text": "white", "sub_face": "#061A12", "sub_edge": "#34D399", "sub_text": "#6EE7B7"},
#             {"box": "#F59E0B", "text": "#000",   "sub_face": "#1A1200", "sub_edge": "#FCD34D", "sub_text": "#FCD34D"},
#             {"box": "#EF4444", "text": "white", "sub_face": "#1A0505", "sub_edge": "#F87171", "sub_text": "#FCA5A5"},
#             {"box": "#EC4899", "text": "white", "sub_face": "#1A0512", "sub_edge": "#F472B6", "sub_text": "#F9A8D4"},
#         ],
#         "line_alpha": 0.75, "sub_shape": "rounded_rect",
#     },
#     {
#         "name": "Blueprint",
#         "bg": "#1E3A5F", "fig_bg": "#1E3A5F",
#         "center_bg": "#FFFFFF", "center_text": "#1E3A5F",
#         "branch_colors": [
#             {"box": "#FFFFFF", "text": "#1E3A5F", "sub_face": "#1E3A5F", "sub_edge": "#FFFFFF", "sub_text": "#FFFFFF"},
#             {"box": "#60A5FA", "text": "#0C1A2E", "sub_face": "#1E3A5F", "sub_edge": "#60A5FA", "sub_text": "#93C5FD"},
#             {"box": "#34D399", "text": "#0A1A14", "sub_face": "#1E3A5F", "sub_edge": "#34D399", "sub_text": "#6EE7B7"},
#             {"box": "#FBBF24", "text": "#1A1000", "sub_face": "#1E3A5F", "sub_edge": "#FBBF24", "sub_text": "#FCD34D"},
#             {"box": "#F87171", "text": "#1A0505", "sub_face": "#1E3A5F", "sub_edge": "#F87171", "sub_text": "#FCA5A5"},
#             {"box": "#E879F9", "text": "#1A0030", "sub_face": "#1E3A5F", "sub_edge": "#E879F9", "sub_text": "#F0ABFC"},
#         ],
#         "line_alpha": 0.6, "sub_shape": "rect",
#     },
#     {
#         "name": "Forest",
#         "bg": "#F4F9F4", "fig_bg": "#F4F9F4",
#         "center_bg": "#2D5A27", "center_text": "white",
#         "branch_colors": [
#             {"box": "#2D5A27", "text": "white", "sub_face": "#EEF7EE", "sub_edge": "#2D5A27", "sub_text": "#1A3A16"},
#             {"box": "#4A7C59", "text": "white", "sub_face": "#F2F8F4", "sub_edge": "#4A7C59", "sub_text": "#2D5A27"},
#             {"box": "#6B8F71", "text": "white", "sub_face": "#F4F9F5", "sub_edge": "#6B8F71", "sub_text": "#2A4A2E"},
#             {"box": "#344E41", "text": "white", "sub_face": "#EEF5EF", "sub_edge": "#344E41", "sub_text": "#1A2E1C"},
#             {"box": "#8FBC8F", "text": "#2D4A29", "sub_face": "#F8FDF8", "sub_edge": "#8FBC8F", "sub_text": "#2D4A29"},
#             {"box": "#A5C8A0", "text": "#2D4A29", "sub_face": "#F8FCF8", "sub_edge": "#A5C8A0", "sub_text": "#2D4A29"},
#         ],
#         "line_alpha": 0.65, "sub_shape": "ellipse",
#     },
#     {
#         "name": "Sunset",
#         "bg": "#1A0520", "fig_bg": "#1A0520",
#         "center_bg": "#FF6B6B", "center_text": "white",
#         "branch_colors": [
#             {"box": "#FF6B6B", "text": "white", "sub_face": "#2A0A0A", "sub_edge": "#FF6B6B", "sub_text": "#FFB3B3"},
#             {"box": "#FF8E53", "text": "white", "sub_face": "#2A1200", "sub_edge": "#FF8E53", "sub_text": "#FFCBA4"},
#             {"box": "#FFD166", "text": "#1A1000", "sub_face": "#2A2000", "sub_edge": "#FFD166", "sub_text": "#FFE9A0"},
#             {"box": "#C77DFF", "text": "white", "sub_face": "#1A0030", "sub_edge": "#C77DFF", "sub_text": "#E9C0FF"},
#             {"box": "#4CC9F0", "text": "#001A20", "sub_face": "#00202A", "sub_edge": "#4CC9F0", "sub_text": "#A0E8FF"},
#             {"box": "#F72585", "text": "white", "sub_face": "#2A0015", "sub_edge": "#F72585", "sub_text": "#FFAAD4"},
#         ],
#         "line_alpha": 0.7, "sub_shape": "rounded_rect",
#     },
# ]


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


# async def generate_mindmap_data(
#     prompt: str,
#     student_id: str = None,
#     format: str = "png",
#     upload_to_s3: bool = True
# ) -> dict:
#     try:
#         mindmap_structure = await get_mindmap_structure(prompt)
#         theme = random.choice(THEMES)
#         logger.info(f"Using theme: {theme['name']}")

#         image_data = create_mindmap_image(mindmap_structure, theme)
#         total_nodes = count_nodes(mindmap_structure)
#         image_bytes = base64.b64decode(image_data)

#         result = {
#             "topic": mindmap_structure["topic"],
#             "total_nodes": total_nodes,
#             "format": format,
#             "theme": theme["name"],
#         }

#         if upload_to_s3:
#             from app.services.s3_service import upload_mindmap_to_s3 as s3_upload
#             s3_url = await s3_upload(
#                 image_bytes=image_bytes,
#                 student_id=student_id,
#                 topic=mindmap_structure["topic"],
#                 format=format
#             )
#             result["s3_url"] = s3_url
#             result["image_url"] = s3_url
#         else:
#             result["image_base64"] = image_data
#             result["image_url"] = f"data:image/png;base64,{image_data}"

#         return result

#     except json.JSONDecodeError as e:
#         logger.error(f"Failed to parse AI response: {e}")
#         raise ValueError("Invalid mind map structure received")
#     except Exception as e:
#         logger.error(f"Error generating mind map: {e}")
#         raise


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


# def hex_to_rgb(hex_color: str):
#     h = hex_color.lstrip('#')
#     return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


# def wrap_text(text: str, max_chars: int) -> list:
#     words = text.split()
#     lines = []
#     current = ""
#     for word in words:
#         if len(current) == 0:
#             current = word
#         elif len(current) + 1 + len(word) <= max_chars:
#             current += " " + word
#         else:
#             lines.append(current)
#             current = word
#     if current:
#         lines.append(current)
#     return lines if lines else [text]


# def compute_positions(branches, cx, cy, branch_r, sub_r):
#     n = len(branches)
#     branch_positions = []
#     sub_positions = []

#     for i, branch in enumerate(branches):
#         angle = (2 * math.pi * i / n) - math.pi / 2
#         bx = cx + branch_r * math.cos(angle)
#         by = cy + branch_r * math.sin(angle)
#         branch_positions.append((bx, by, angle))

#         subs = branch.get("subbranches", [])
#         ns = len(subs)
#         sub_pos_for_branch = []

#         if ns == 0:
#             sub_positions.append([])
#             continue

#         fan_span = min(math.pi * 0.5, math.pi * 0.18 * ns)

#         for j in range(ns):
#             if ns == 1:
#                 sa = angle
#             else:
#                 sa = angle - fan_span / 2 + j * (fan_span / (ns - 1))
#             sx = bx + sub_r * math.cos(sa)
#             sy = by + sub_r * math.sin(sa)
#             sub_pos_for_branch.append((sx, sy))

#         sub_positions.append(sub_pos_for_branch)

#     return branch_positions, sub_positions


# def draw_bezier(ax, x1, y1, x2, y2, color, lw=2.5, alpha=0.75):
#     mx, my = (x1 + x2) / 2, (y1 + y2) / 2
#     dx, dy = x2 - x1, y2 - y1
#     offset = min(abs(dx) + abs(dy), 0.3) * 0.12
#     cpx = mx - dy * offset
#     cpy = my + dx * offset
#     verts = [(x1, y1), (cpx, cpy), (x2, y2)]
#     codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
#     path = Path(verts, codes)
#     patch = patches.PathPatch(
#         path, facecolor='none', edgecolor=color,
#         linewidth=lw, alpha=alpha, zorder=1, capstyle='round'
#     )
#     ax.add_patch(patch)


# def draw_center_node(ax, cx, cy, topic, theme, radius=0.55):
#     bg = hex_to_rgb(theme["center_bg"])
#     tc = theme["center_text"]
#     glow = plt.Circle((cx, cy), radius + 0.12, color=bg, alpha=0.2, zorder=3)
#     ax.add_patch(glow)
#     circle = plt.Circle((cx, cy), radius, color=bg, zorder=4)
#     ax.add_patch(circle)
#     ring = plt.Circle((cx, cy), radius - 0.06, color='none',
#                       edgecolor=tc, linewidth=0.8, alpha=0.25, zorder=5)
#     ax.add_patch(ring)
#     lines = wrap_text(topic, 12)
#     n = len(lines)
#     for i, line in enumerate(lines):
#         y_offset = (i - (n - 1) / 2) * 0.13
#         ax.text(cx, cy + y_offset, line,
#                 ha='center', va='center',
#                 fontsize=11, fontweight='bold',
#                 color=tc, zorder=6,
#                 path_effects=[pe.withStroke(linewidth=2, foreground=theme["center_bg"])])


# def draw_branch_node(ax, bx, by, name, color, sub_shape):
#     bw, bh = 1.25, 0.46
#     box_color = hex_to_rgb(color["box"])
#     text_color = color["text"]
#     shadow = FancyBboxPatch(
#         (bx - bw/2 + 0.03, by - bh/2 - 0.03), bw, bh,
#         boxstyle="round,pad=0.05",
#         facecolor=(0, 0, 0, 0.18), edgecolor='none', zorder=4
#     )
#     ax.add_patch(shadow)
#     box = FancyBboxPatch(
#         (bx - bw/2, by - bh/2), bw, bh,
#         boxstyle="round,pad=0.05",
#         facecolor=box_color, edgecolor='none',
#         linewidth=0, zorder=5
#     )
#     ax.add_patch(box)
#     lines = wrap_text(name, 14)
#     n = len(lines)
#     fs = 9.5 if n == 1 else 8.5
#     for i, line in enumerate(lines):
#         y_offset = (i - (n - 1) / 2) * 0.14
#         ax.text(bx, by + y_offset, line,
#                 ha='center', va='center',
#                 fontsize=fs, fontweight='bold',
#                 color=text_color, zorder=6)


# def draw_sub_node(ax, sx, sy, name, color, sub_shape):
#     sw, sh = 1.1, 0.38
#     sub_face = hex_to_rgb(color["sub_face"])
#     sub_edge = hex_to_rgb(color["sub_edge"])
#     sub_text = color["sub_text"]

#     if sub_shape == "ellipse":
#         node = mpatches.Ellipse(
#             (sx, sy), width=sw, height=sh,
#             facecolor=sub_face, edgecolor=sub_edge,
#             linewidth=1.8, zorder=5
#         )
#         ax.add_patch(node)
#     elif sub_shape == "rect":
#         node = plt.Rectangle(
#             (sx - sw/2, sy - sh/2), sw, sh,
#             facecolor=sub_face, edgecolor=sub_edge,
#             linewidth=1.5, zorder=5
#         )
#         ax.add_patch(node)
#     else:
#         node = FancyBboxPatch(
#             (sx - sw/2, sy - sh/2), sw, sh,
#             boxstyle="round,pad=0.04",
#             facecolor=sub_face, edgecolor=sub_edge,
#             linewidth=1.8, zorder=5
#         )
#         ax.add_patch(node)

#     lines = wrap_text(name, 13)
#     n = len(lines)
#     fs = 7.5 if n == 1 else 6.8
#     for i, line in enumerate(lines):
#         y_offset = (i - (n - 1) / 2) * 0.11
#         ax.text(sx, sy + y_offset, line,
#                 ha='center', va='center',
#                 fontsize=fs, fontweight='semibold',
#                 color=sub_text, zorder=6)


# def _grid_color(bg_hex):
#     r, g, b = hex_to_rgb(bg_hex)
#     lum = 0.299 * r + 0.587 * g + 0.114 * b
#     f = 0.88 if lum > 0.5 else 1.15
#     return (min(1.0, max(0.0, r*f)), min(1.0, max(0.0, g*f)), min(1.0, max(0.0, b*f)))


# def _contrast_color(bg_hex):
#     r, g, b = hex_to_rgb(bg_hex)
#     lum = 0.299 * r + 0.587 * g + 0.114 * b
#     return "#1a1a1a" if lum > 0.5 else "#f0f0f0"


# def create_mindmap_image(data: dict, theme: dict) -> str:
#     topic = data.get("topic", "Mind Map")
#     branches = data.get("branches", [])
#     n = len(branches)

#     if n == 0:
#         return _create_empty(topic, theme)

#     FW, FH, DPI = 20, 13, 150
#     fig, ax = plt.subplots(figsize=(FW, FH))
#     fig.patch.set_facecolor(theme["fig_bg"])
#     ax.set_facecolor(theme["bg"])
#     ax.set_xlim(-7.5, 7.5)
#     ax.set_ylim(-4.8, 4.8)
#     ax.set_aspect('equal')
#     ax.axis('off')

#     grid_color = _grid_color(theme["bg"])
#     for gx in range(-7, 8):
#         for gy in range(-4, 5):
#             ax.plot(gx, gy, 'o', color=grid_color, markersize=1.5, alpha=0.5, zorder=0)

#     cx, cy = 0.0, 0.0
#     branch_r = max(2.4, min(3.2, 9.0 / n))
#     sub_r = max(1.5, min(2.0, 6.0 / n))

#     branch_pos, sub_pos = compute_positions(branches, cx, cy, branch_r, sub_r)

#     for i, branch in enumerate(branches):
#         bx, by, angle = branch_pos[i]
#         color = theme["branch_colors"][i % len(theme["branch_colors"])]
#         line_col = color["box"]
#         draw_bezier(ax, cx, cy, bx, by, line_col, lw=3.0, alpha=theme["line_alpha"])
#         for sx, sy in sub_pos[i]:
#             draw_bezier(ax, bx, by, sx, sy, line_col, lw=1.8, alpha=theme["line_alpha"] * 0.75)

#     sub_shape = theme.get("sub_shape", "rounded_rect")
#     for i, branch in enumerate(branches):
#         color = theme["branch_colors"][i % len(theme["branch_colors"])]
#         subs = branch.get("subbranches", [])
#         for j, (sx, sy) in enumerate(sub_pos[i]):
#             if j < len(subs):
#                 draw_sub_node(ax, sx, sy, subs[j], color, sub_shape)

#     for i, branch in enumerate(branches):
#         bx, by, angle = branch_pos[i]
#         color = theme["branch_colors"][i % len(theme["branch_colors"])]
#         draw_branch_node(ax, bx, by, branch.get("name", ""), color, sub_shape)

#     draw_center_node(ax, cx, cy, topic, theme, radius=0.55)

#     title_color = _contrast_color(theme["bg"])
#     fig.text(0.5, 0.97, topic, ha='center', va='top',
#              fontsize=18, fontweight='bold', color=title_color,
#              path_effects=[pe.withStroke(linewidth=3, foreground=theme["bg"])])
#     fig.text(0.98, 0.01, f"Theme: {theme['name']}",
#              ha='right', va='bottom', fontsize=8, color=title_color, alpha=0.35)

#     plt.tight_layout(pad=0.4)
#     buf = io.BytesIO()
#     plt.savefig(buf, format='PNG', dpi=DPI, bbox_inches='tight',
#                 facecolor=fig.get_facecolor())
#     plt.close(fig)
#     buf.seek(0)
#     return base64.b64encode(buf.getvalue()).decode('utf-8')


# def _create_empty(topic, theme):
#     fig, ax = plt.subplots(figsize=(10, 7))
#     fig.patch.set_facecolor(theme["fig_bg"])
#     ax.set_facecolor(theme["bg"])
#     ax.axis('off')
#     circle = plt.Circle((0.5, 0.5), 0.22,
#                         color=hex_to_rgb(theme["center_bg"]),
#                         transform=ax.transAxes, zorder=5)
#     ax.add_patch(circle)
#     ax.text(0.5, 0.5, topic, ha='center', va='center',
#             fontsize=16, fontweight='bold',
#             color=theme["center_text"],
#             transform=ax.transAxes, zorder=6)
#     buf = io.BytesIO()
#     plt.savefig(buf, format='PNG', dpi=120, bbox_inches='tight')
#     plt.close(fig)
#     buf.seek(0)
#     return base64.b64encode(buf.getvalue()).decode('utf-8')





import google.generativeai as genai
from app.config import settings
import json
import base64
import io
import math
import random
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe
from matplotlib.path import Path
import matplotlib.patches as patches

logger = logging.getLogger(__name__)

AI_PROVIDER = None
gemini_model = None
openai_client = None


def initialize_ai():
    global AI_PROVIDER, gemini_model, openai_client
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    if gemini_key:
        genai.configure(api_key=gemini_key, transport='rest')
        gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        AI_PROVIDER = "gemini"
        logger.info("Using Gemini: gemini-2.0-flash REST")
        return
    openai_key = getattr(settings, 'OPENAI_API_KEY', None)
    if openai_key:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_key)
            AI_PROVIDER = "openai"
            logger.info("Using OpenAI GPT fallback")
            return
        except Exception as e:
            logger.warning(f"OpenAI init failed: {e}")
    logger.error("No AI provider available")


initialize_ai()


THEMES = [
    {
        "name": "Corporate",
        "bg": "#FFFFFF", "fig_bg": "#F8F9FA",
        "center_bg": "#1A1A2E", "center_text": "white",
        "branch_colors": [
            {"box": "#2563EB", "text": "white", "sub_face": "#EFF6FF", "sub_edge": "#2563EB", "sub_text": "#1E3A8A"},
            {"box": "#16A34A", "text": "white", "sub_face": "#F0FDF4", "sub_edge": "#16A34A", "sub_text": "#14532D"},
            {"box": "#DC2626", "text": "white", "sub_face": "#FEF2F2", "sub_edge": "#DC2626", "sub_text": "#7F1D1D"},
            {"box": "#7C3AED", "text": "white", "sub_face": "#F5F3FF", "sub_edge": "#7C3AED", "sub_text": "#4C1D95"},
            {"box": "#0891B2", "text": "white", "sub_face": "#ECFEFF", "sub_edge": "#0891B2", "sub_text": "#164E63"},
            {"box": "#EA580C", "text": "white", "sub_face": "#FFF7ED", "sub_edge": "#EA580C", "sub_text": "#7C2D12"},
        ],
        "line_alpha": 0.7, "sub_shape": "rounded_rect",
    },
    {
        "name": "Pastel",
        "bg": "#FDF6EC", "fig_bg": "#FDF6EC",
        "center_bg": "#4A4A4A", "center_text": "white",
        "branch_colors": [
            {"box": "#F4A261", "text": "white", "sub_face": "#FFF8F0", "sub_edge": "#F4A261", "sub_text": "#7B3F00"},
            {"box": "#E76F51", "text": "white", "sub_face": "#FFF5F2", "sub_edge": "#E76F51", "sub_text": "#7F1D1D"},
            {"box": "#2A9D8F", "text": "white", "sub_face": "#F0FAFA", "sub_edge": "#2A9D8F", "sub_text": "#134E4A"},
            {"box": "#264653", "text": "white", "sub_face": "#EEF4F8", "sub_edge": "#264653", "sub_text": "#1E3A5F"},
            {"box": "#E9C46A", "text": "#3A2800", "sub_face": "#FFFBEA", "sub_edge": "#E9C46A", "sub_text": "#5C4000"},
            {"box": "#A8DADC", "text": "#1A3A3C", "sub_face": "#F0FBFC", "sub_edge": "#A8DADC", "sub_text": "#1A4A4C"},
        ],
        "line_alpha": 0.6, "sub_shape": "ellipse",
    },
    {
        "name": "Dark Neon",
        "bg": "#0D0D1A", "fig_bg": "#0D0D1A",
        "center_bg": "#1A1A2E", "center_text": "#E9D5FF",
        "branch_colors": [
            {"box": "#7C3AED", "text": "white", "sub_face": "#13102A", "sub_edge": "#A78BFA", "sub_text": "#C4B5FD"},
            {"box": "#0EA5E9", "text": "white", "sub_face": "#07192E", "sub_edge": "#38BDF8", "sub_text": "#7DD3FC"},
            {"box": "#10B981", "text": "white", "sub_face": "#061A12", "sub_edge": "#34D399", "sub_text": "#6EE7B7"},
            {"box": "#F59E0B", "text": "#000",   "sub_face": "#1A1200", "sub_edge": "#FCD34D", "sub_text": "#FCD34D"},
            {"box": "#EF4444", "text": "white", "sub_face": "#1A0505", "sub_edge": "#F87171", "sub_text": "#FCA5A5"},
            {"box": "#EC4899", "text": "white", "sub_face": "#1A0512", "sub_edge": "#F472B6", "sub_text": "#F9A8D4"},
        ],
        "line_alpha": 0.75, "sub_shape": "rounded_rect",
    },
    {
        "name": "Blueprint",
        "bg": "#1E3A5F", "fig_bg": "#1E3A5F",
        "center_bg": "#FFFFFF", "center_text": "#1E3A5F",
        "branch_colors": [
            {"box": "#FFFFFF", "text": "#1E3A5F", "sub_face": "#1E3A5F", "sub_edge": "#FFFFFF", "sub_text": "#FFFFFF"},
            {"box": "#60A5FA", "text": "#0C1A2E", "sub_face": "#1E3A5F", "sub_edge": "#60A5FA", "sub_text": "#93C5FD"},
            {"box": "#34D399", "text": "#0A1A14", "sub_face": "#1E3A5F", "sub_edge": "#34D399", "sub_text": "#6EE7B7"},
            {"box": "#FBBF24", "text": "#1A1000", "sub_face": "#1E3A5F", "sub_edge": "#FBBF24", "sub_text": "#FCD34D"},
            {"box": "#F87171", "text": "#1A0505", "sub_face": "#1E3A5F", "sub_edge": "#F87171", "sub_text": "#FCA5A5"},
            {"box": "#E879F9", "text": "#1A0030", "sub_face": "#1E3A5F", "sub_edge": "#E879F9", "sub_text": "#F0ABFC"},
        ],
        "line_alpha": 0.6, "sub_shape": "rect",
    },
    {
        "name": "Forest",
        "bg": "#F4F9F4", "fig_bg": "#F4F9F4",
        "center_bg": "#2D5A27", "center_text": "white",
        "branch_colors": [
            {"box": "#2D5A27", "text": "white", "sub_face": "#EEF7EE", "sub_edge": "#2D5A27", "sub_text": "#1A3A16"},
            {"box": "#4A7C59", "text": "white", "sub_face": "#F2F8F4", "sub_edge": "#4A7C59", "sub_text": "#2D5A27"},
            {"box": "#6B8F71", "text": "white", "sub_face": "#F4F9F5", "sub_edge": "#6B8F71", "sub_text": "#2A4A2E"},
            {"box": "#344E41", "text": "white", "sub_face": "#EEF5EF", "sub_edge": "#344E41", "sub_text": "#1A2E1C"},
            {"box": "#8FBC8F", "text": "#2D4A29", "sub_face": "#F8FDF8", "sub_edge": "#8FBC8F", "sub_text": "#2D4A29"},
            {"box": "#A5C8A0", "text": "#2D4A29", "sub_face": "#F8FCF8", "sub_edge": "#A5C8A0", "sub_text": "#2D4A29"},
        ],
        "line_alpha": 0.65, "sub_shape": "ellipse",
    },
    {
        "name": "Sunset",
        "bg": "#1A0520", "fig_bg": "#1A0520",
        "center_bg": "#FF6B6B", "center_text": "white",
        "branch_colors": [
            {"box": "#FF6B6B", "text": "white", "sub_face": "#2A0A0A", "sub_edge": "#FF6B6B", "sub_text": "#FFB3B3"},
            {"box": "#FF8E53", "text": "white", "sub_face": "#2A1200", "sub_edge": "#FF8E53", "sub_text": "#FFCBA4"},
            {"box": "#FFD166", "text": "#1A1000", "sub_face": "#2A2000", "sub_edge": "#FFD166", "sub_text": "#FFE9A0"},
            {"box": "#C77DFF", "text": "white", "sub_face": "#1A0030", "sub_edge": "#C77DFF", "sub_text": "#E9C0FF"},
            {"box": "#4CC9F0", "text": "#001A20", "sub_face": "#00202A", "sub_edge": "#4CC9F0", "sub_text": "#A0E8FF"},
            {"box": "#F72585", "text": "white", "sub_face": "#2A0015", "sub_edge": "#F72585", "sub_text": "#FFAAD4"},
        ],
        "line_alpha": 0.7, "sub_shape": "rounded_rect",
    },
]


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


async def generate_mindmap_data(
    prompt: str,
    student_id: str = None,
    format: str = "png",
) -> dict:
    try:
        mindmap_structure = await get_mindmap_structure(prompt)
        theme = random.choice(THEMES)
        logger.info(f"Using theme: {theme['name']}")

        image_data = create_mindmap_image(mindmap_structure, theme)
        total_nodes = count_nodes(mindmap_structure)

        # Save to MongoDB
        mongo_id = await save_mindmap_to_mongo(
            student_id=student_id,
            prompt=prompt,
            topic=mindmap_structure["topic"],
            image_base64=image_data,
            total_nodes=total_nodes,
            theme=theme["name"],
        )

        return {
            "topic": mindmap_structure["topic"],
            "total_nodes": total_nodes,
            "format": format,
            "theme": theme["name"],
            "mongo_id": mongo_id,
            "image_base64": image_data,
            "image_url": f"data:image/png;base64,{image_data}",
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        raise ValueError("Invalid mind map structure received")
    except Exception as e:
        logger.error(f"Error generating mind map: {e}")
        raise


async def save_mindmap_to_mongo(
    student_id: str,
    prompt: str,
    topic: str,
    image_base64: str,
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
            "image_base64": image_base64,
            "total_nodes": total_nodes,
            "theme": theme,
            "created_at": datetime.utcnow(),
        }
        result = await db["mindmaps"].insert_one(doc)
        logger.info(f"Saved mindmap to MongoDB: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.warning(f"MongoDB save failed (non-critical): {e}")
        return "not_saved"


async def get_mindmap_structure(prompt: str) -> dict:
    if AI_PROVIDER == "gemini":
        return await _get_structure_gemini(prompt)
    elif AI_PROVIDER == "openai":
        return await _get_structure_openai(prompt)
    else:
        raise RuntimeError("No AI provider available.")


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
        logger.error(f"Gemini failed: {e}")
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
        logger.error(f"OpenAI failed: {e}")
        raise


def _parse_json_response(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()
    data = json.loads(content)
    if "topic" not in data or "branches" not in data:
        raise ValueError("Invalid mind map structure")
    if not isinstance(data["branches"], list):
        raise ValueError("Branches must be a list")
    return data


def count_nodes(structure: dict) -> int:
    total = 1
    for branch in structure.get("branches", []):
        total += 1
        total += len(branch.get("subbranches", []))
    return total


def hex_to_rgb(hex_color: str):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def wrap_text(text: str, max_chars: int) -> list:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) == 0:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [text]


def compute_positions(branches, cx, cy, branch_r, sub_r):
    n = len(branches)
    branch_positions = []
    sub_positions = []
    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / n) - math.pi / 2
        bx = cx + branch_r * math.cos(angle)
        by = cy + branch_r * math.sin(angle)
        branch_positions.append((bx, by, angle))
        subs = branch.get("subbranches", [])
        ns = len(subs)
        sub_pos_for_branch = []
        if ns == 0:
            sub_positions.append([])
            continue
        fan_span = min(math.pi * 0.5, math.pi * 0.18 * ns)
        for j in range(ns):
            if ns == 1:
                sa = angle
            else:
                sa = angle - fan_span / 2 + j * (fan_span / (ns - 1))
            sx = bx + sub_r * math.cos(sa)
            sy = by + sub_r * math.sin(sa)
            sub_pos_for_branch.append((sx, sy))
        sub_positions.append(sub_pos_for_branch)
    return branch_positions, sub_positions


def draw_bezier(ax, x1, y1, x2, y2, color, lw=2.5, alpha=0.75):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    offset = min(abs(dx) + abs(dy), 0.3) * 0.12
    cpx = mx - dy * offset
    cpy = my + dx * offset
    verts = [(x1, y1), (cpx, cpy), (x2, y2)]
    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
    path = Path(verts, codes)
    patch = patches.PathPatch(path, facecolor='none', edgecolor=color,
                               linewidth=lw, alpha=alpha, zorder=1, capstyle='round')
    ax.add_patch(patch)


def draw_center_node(ax, cx, cy, topic, theme, radius=0.55):
    bg = hex_to_rgb(theme["center_bg"])
    tc = theme["center_text"]
    ax.add_patch(plt.Circle((cx, cy), radius + 0.12, color=bg, alpha=0.2, zorder=3))
    ax.add_patch(plt.Circle((cx, cy), radius, color=bg, zorder=4))
    ax.add_patch(plt.Circle((cx, cy), radius - 0.06, color='none',
                             edgecolor=tc, linewidth=0.8, alpha=0.25, zorder=5))
    lines = wrap_text(topic, 12)
    n = len(lines)
    for i, line in enumerate(lines):
        y_offset = (i - (n - 1) / 2) * 0.13
        ax.text(cx, cy + y_offset, line, ha='center', va='center',
                fontsize=11, fontweight='bold', color=tc, zorder=6,
                path_effects=[pe.withStroke(linewidth=2, foreground=theme["center_bg"])])


def draw_branch_node(ax, bx, by, name, color, sub_shape):
    bw, bh = 1.25, 0.46
    box_color = hex_to_rgb(color["box"])
    ax.add_patch(FancyBboxPatch((bx - bw/2 + 0.03, by - bh/2 - 0.03), bw, bh,
                                 boxstyle="round,pad=0.05",
                                 facecolor=(0, 0, 0, 0.18), edgecolor='none', zorder=4))
    ax.add_patch(FancyBboxPatch((bx - bw/2, by - bh/2), bw, bh,
                                 boxstyle="round,pad=0.05",
                                 facecolor=box_color, edgecolor='none', linewidth=0, zorder=5))
    lines = wrap_text(name, 14)
    n = len(lines)
    fs = 9.5 if n == 1 else 8.5
    for i, line in enumerate(lines):
        y_offset = (i - (n - 1) / 2) * 0.14
        ax.text(bx, by + y_offset, line, ha='center', va='center',
                fontsize=fs, fontweight='bold', color=color["text"], zorder=6)


def draw_sub_node(ax, sx, sy, name, color, sub_shape):
    sw, sh = 1.1, 0.38
    sub_face = hex_to_rgb(color["sub_face"])
    sub_edge = hex_to_rgb(color["sub_edge"])
    if sub_shape == "ellipse":
        ax.add_patch(mpatches.Ellipse((sx, sy), width=sw, height=sh,
                                       facecolor=sub_face, edgecolor=sub_edge,
                                       linewidth=1.8, zorder=5))
    elif sub_shape == "rect":
        ax.add_patch(plt.Rectangle((sx - sw/2, sy - sh/2), sw, sh,
                                    facecolor=sub_face, edgecolor=sub_edge,
                                    linewidth=1.5, zorder=5))
    else:
        ax.add_patch(FancyBboxPatch((sx - sw/2, sy - sh/2), sw, sh,
                                     boxstyle="round,pad=0.04",
                                     facecolor=sub_face, edgecolor=sub_edge,
                                     linewidth=1.8, zorder=5))
    lines = wrap_text(name, 13)
    n = len(lines)
    fs = 7.5 if n == 1 else 6.8
    for i, line in enumerate(lines):
        y_offset = (i - (n - 1) / 2) * 0.11
        ax.text(sx, sy + y_offset, line, ha='center', va='center',
                fontsize=fs, fontweight='semibold', color=color["sub_text"], zorder=6)


def _grid_color(bg_hex):
    r, g, b = hex_to_rgb(bg_hex)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    f = 0.88 if lum > 0.5 else 1.15
    return (min(1.0, max(0.0, r*f)), min(1.0, max(0.0, g*f)), min(1.0, max(0.0, b*f)))


def _contrast_color(bg_hex):
    r, g, b = hex_to_rgb(bg_hex)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return "#1a1a1a" if lum > 0.5 else "#f0f0f0"


def create_mindmap_image(data: dict, theme: dict) -> str:
    topic = data.get("topic", "Mind Map")
    branches = data.get("branches", [])
    n = len(branches)
    if n == 0:
        return _create_empty(topic, theme)
    FW, FH, DPI = 20, 13, 150
    fig, ax = plt.subplots(figsize=(FW, FH))
    fig.patch.set_facecolor(theme["fig_bg"])
    ax.set_facecolor(theme["bg"])
    ax.set_xlim(-7.5, 7.5)
    ax.set_ylim(-4.8, 4.8)
    ax.set_aspect('equal')
    ax.axis('off')
    grid_color = _grid_color(theme["bg"])
    for gx in range(-7, 8):
        for gy in range(-4, 5):
            ax.plot(gx, gy, 'o', color=grid_color, markersize=1.5, alpha=0.5, zorder=0)
    cx, cy = 0.0, 0.0
    branch_r = max(2.4, min(3.2, 9.0 / n))
    sub_r = max(1.5, min(2.0, 6.0 / n))
    branch_pos, sub_pos = compute_positions(branches, cx, cy, branch_r, sub_r)
    for i, branch in enumerate(branches):
        bx, by, angle = branch_pos[i]
        color = theme["branch_colors"][i % len(theme["branch_colors"])]
        draw_bezier(ax, cx, cy, bx, by, color["box"], lw=3.0, alpha=theme["line_alpha"])
        for sx, sy in sub_pos[i]:
            draw_bezier(ax, bx, by, sx, sy, color["box"], lw=1.8, alpha=theme["line_alpha"] * 0.75)
    sub_shape = theme.get("sub_shape", "rounded_rect")
    for i, branch in enumerate(branches):
        color = theme["branch_colors"][i % len(theme["branch_colors"])]
        subs = branch.get("subbranches", [])
        for j, (sx, sy) in enumerate(sub_pos[i]):
            if j < len(subs):
                draw_sub_node(ax, sx, sy, subs[j], color, sub_shape)
    for i, branch in enumerate(branches):
        bx, by, angle = branch_pos[i]
        color = theme["branch_colors"][i % len(theme["branch_colors"])]
        draw_branch_node(ax, bx, by, branch.get("name", ""), color, sub_shape)
    draw_center_node(ax, cx, cy, topic, theme, radius=0.55)
    title_color = _contrast_color(theme["bg"])
    fig.text(0.5, 0.97, topic, ha='center', va='top', fontsize=18, fontweight='bold',
             color=title_color, path_effects=[pe.withStroke(linewidth=3, foreground=theme["bg"])])
    fig.text(0.98, 0.01, f"Theme: {theme['name']}", ha='right', va='bottom',
             fontsize=8, color=title_color, alpha=0.35)
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    plt.savefig(buf, format='PNG', dpi=DPI, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def _create_empty(topic, theme):
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(theme["fig_bg"])
    ax.set_facecolor(theme["bg"])
    ax.axis('off')
    ax.add_patch(plt.Circle((0.5, 0.5), 0.22, color=hex_to_rgb(theme["center_bg"]),
                             transform=ax.transAxes, zorder=5))
    ax.text(0.5, 0.5, topic, ha='center', va='center', fontsize=16, fontweight='bold',
            color=theme["center_text"], transform=ax.transAxes, zorder=6)
    buf = io.BytesIO()
    plt.savefig(buf, format='PNG', dpi=120, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')