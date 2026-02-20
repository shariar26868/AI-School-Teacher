import os
import fitz  # PyMuPDF
from PIL import Image
import base64
from openai import OpenAI
from docx import Document
from app.config import settings
import asyncio
import re

# Initialize OpenAI client only if API key is available
client = None
if settings.OPENAI_API_KEY:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

def clean_ocr_text(text: str) -> str:
    """
    Clean OCR output by removing markdown artifacts
    """
    # Remove markdown code blocks
    text = re.sub(r'```plaintext\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()


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
    Extract text from ALL pages of PDF using OCR - FORCED ON EVERY PAGE
    """
    def _extract_pdf():
        doc = fitz.open(pdf_path)
        all_pages = []
        
        print(f"📄 Starting OCR for PDF with {len(doc)} pages...")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            print(f"🔍 Processing page {page_num + 1}/{len(doc)} with OCR...")
            
            # Convert page to high-quality image
            mat = fitz.Matrix(3, 3)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Run OCR
            ocr_text = _ocr_image_bytes_sync(img_data)
            
            # Clean the OCR output
            ocr_text = clean_ocr_text(ocr_text)
            
            all_pages.append({
                'page_number': page_num + 1,
                'content': ocr_text,
                'extraction_method': 'ocr'
            })
            
            print(f"✅ Page {page_num + 1} OCR complete - extracted {len(ocr_text)} characters")
        
        doc.close()
        print(f"✅ PDF OCR complete - processed {len(all_pages)} pages")
        return all_pages
    
    return await asyncio.to_thread(_extract_pdf)


async def extract_from_image(image_path: str) -> list:
    """
    Extract text from image using OCR
    """
    def _extract_image():
        print(f"📄 Running OCR on image...")
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
        
        text = _ocr_image_bytes_sync(img_data)
        text = clean_ocr_text(text)
        print(f"✅ Image OCR complete - extracted {len(text)} characters")
        
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
        print(f"📄 Extracting text from DOCX...")
        doc = Document(docx_path)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        
        print(f"✅ DOCX extraction complete - extracted {len(text)} characters")
        
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
        print(f"📄 Reading TXT file...")
        with open(txt_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        print(f"✅ TXT reading complete - extracted {len(text)} characters")
        
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
    if not client:
        raise RuntimeError("OpenAI API key is not configured. Please set OPENAI_API_KEY in your .env file.")
    
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Extract ALL visible text from this document image exactly as it appears.

IMPORTANT RULES:
1. Extract EVERY word, number, and symbol
2. Maintain original formatting and structure
3. Do NOT add markdown formatting (no ```, no **, no ##)
4. Do NOT add code blocks
5. Output plain text only
6. Preserve line breaks and spacing as they appear
7. Include all questions, instructions, and content

Start extraction:"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }],
            max_tokens=4096,
            temperature=0
        )
        
        extracted_text = response.choices[0].message.content
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            print("⚠️ Warning: OCR returned very little text")
            return "[OCR Warning: Minimal text extracted]"
        
        return extracted_text
        
    except Exception as e:
        print(f"❌ OCR Error: {str(e)}")
        return f"[OCR Error: {str(e)}]"


async def ocr_image_bytes(image_bytes: bytes) -> str:
    """
    Async wrapper for OCR
    """
    return await asyncio.to_thread(_ocr_image_bytes_sync, image_bytes)