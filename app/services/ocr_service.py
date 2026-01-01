# import os
# import fitz  # PyMuPDF
# from PIL import Image
# import base64
# from openai import OpenAI
# from docx import Document
# from app.config import settings

# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# async def extract_text_from_file(file_path: str) -> list:
#     """
#     Extract text from any file type (PDF, image, DOCX, TXT)
#     """
#     file_extension = os.path.splitext(file_path)[1].lower()
    
#     if file_extension == '.pdf':
#         return await extract_from_pdf(file_path)
#     elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
#         return await extract_from_image(file_path)
#     elif file_extension == '.docx':
#         return await extract_from_docx(file_path)
#     elif file_extension == '.txt':
#         return await extract_from_txt(file_path)
#     else:
#         raise ValueError(f"Unsupported file format: {file_extension}")


# async def extract_from_pdf(pdf_path: str) -> list:
#     """
#     Extract text from all pages of PDF
#     """
#     doc = fitz.open(pdf_path)
#     all_pages = []
    
#     for page_num in range(len(doc)):
#         page = doc[page_num]
        
#         # Try direct text extraction first
#         text = page.get_text()
        
#         if text.strip():
#             all_pages.append({
#                 'page_number': page_num + 1,
#                 'content': text,
#                 'extraction_method': 'direct'
#             })
#         else:
#             # Convert page to image and use OCR
#             pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
#             img_data = pix.tobytes("png")
            
#             ocr_text = await ocr_image_bytes(img_data)
#             all_pages.append({
#                 'page_number': page_num + 1,
#                 'content': ocr_text,
#                 'extraction_method': 'ocr'
#             })
    
#     doc.close()
#     return all_pages


# async def extract_from_image(image_path: str) -> list:
#     """
#     Extract text from image using OCR
#     """
#     with open(image_path, 'rb') as img_file:
#         img_data = img_file.read()
    
#     text = await ocr_image_bytes(img_data)
#     return [{
#         'page_number': 1,
#         'content': text,
#         'extraction_method': 'ocr'
#     }]


# async def extract_from_docx(docx_path: str) -> list:
#     """
#     Extract text from DOCX file
#     """
#     doc = Document(docx_path)
#     text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    
#     return [{
#         'page_number': 1,
#         'content': text,
#         'extraction_method': 'direct'
#     }]


# async def extract_from_txt(txt_path: str) -> list:
#     """
#     Extract text from TXT file
#     """
#     with open(txt_path, 'r', encoding='utf-8') as file:
#         text = file.read()
    
#     return [{
#         'page_number': 1,
#         'content': text,
#         'extraction_method': 'direct'
#     }]


# async def ocr_image_bytes(image_bytes: bytes) -> str:
#     """
#     Use GPT-4 Vision to extract text from image
#     """
#     base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{
#             "role": "user",
#             "content": [
#                 {
#                     "type": "text",
#                     "text": """Extract ALL text from this assignment accurately. Include:
#                     - All questions with their numbers
#                     - Instructions
#                     - Mathematical formulas (use LaTeX if needed)
#                     - Tables and diagrams descriptions
#                     - Any notes or annotations
                    
#                     Maintain original structure and formatting."""
#                 },
#                 {
#                     "type": "image_url",
#                     "image_url": {
#                         "url": f"data:image/png;base64,{base64_image}"
#                     }
#                 }
#             ]
#         }],
#         max_tokens=4096
#     )
    
#     return response.choices[0].message.content




import os
import fitz  # PyMuPDF
from PIL import Image
import base64
from openai import OpenAI
from docx import Document
from app.config import settings
import asyncio

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def extract_text_from_file(file_path: str) -> list:
    """
    Extract text from any file type (PDF, image, DOCX, TXT)
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return await extract_from_pdf(file_path)
    elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
        return await extract_from_image(file_path)
    elif file_extension == '.docx':
        return await extract_from_docx(file_path)
    elif file_extension == '.txt':
        return await extract_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")


async def extract_from_pdf(pdf_path: str) -> list:
    """
    Extract text from all pages of PDF
    """
    def _extract_pdf():
        doc = fitz.open(pdf_path)
        all_pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Try direct text extraction first
            text = page.get_text()
            
            if text.strip():
                all_pages.append({
                    'page_number': page_num + 1,
                    'content': text,
                    'extraction_method': 'direct'
                })
            else:
                # Convert page to image and use OCR
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                
                # Run OCR synchronously within thread
                ocr_text = _ocr_image_bytes_sync(img_data)
                all_pages.append({
                    'page_number': page_num + 1,
                    'content': ocr_text,
                    'extraction_method': 'ocr'
                })
        
        doc.close()
        return all_pages
    
    # Run the entire PDF extraction in a thread
    return await asyncio.to_thread(_extract_pdf)


async def extract_from_image(image_path: str) -> list:
    """
    Extract text from image using OCR
    """
    def _extract_image():
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
        
        text = _ocr_image_bytes_sync(img_data)
        return [{
            'page_number': 1,
            'content': text,
            'extraction_method': 'ocr'
        }]
    
    return await asyncio.to_thread(_extract_image)


async def extract_from_docx(docx_path: str) -> list:
    """
    Extract text from DOCX file
    """
    def _extract_docx():
        doc = Document(docx_path)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        
        return [{
            'page_number': 1,
            'content': text,
            'extraction_method': 'direct'
        }]
    
    return await asyncio.to_thread(_extract_docx)


async def extract_from_txt(txt_path: str) -> list:
    """
    Extract text from TXT file
    """
    def _extract_txt():
        with open(txt_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        return [{
            'page_number': 1,
            'content': text,
            'extraction_method': 'direct'
        }]
    
    return await asyncio.to_thread(_extract_txt)


def _ocr_image_bytes_sync(image_bytes: bytes) -> str:
    """
    Use GPT-4 Vision to extract text from image (SYNCHRONOUS)
    """
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Extract ALL text from this assignment accurately. Include:
                    - All questions with their numbers
                    - Instructions
                    - Mathematical formulas (use LaTeX if needed)
                    - Tables and diagrams descriptions
                    - Any notes or annotations
                    
                    Maintain original structure and formatting."""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }],
        max_tokens=4096
    )
    
    return response.choices[0].message.content


async def ocr_image_bytes(image_bytes: bytes) -> str:
    """
    Async wrapper for OCR (for backward compatibility)
    """
    return await asyncio.to_thread(_ocr_image_bytes_sync, image_bytes)