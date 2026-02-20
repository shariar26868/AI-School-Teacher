import os
from typing import Optional
from datetime import datetime
import hashlib

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    """
    return os.path.splitext(filename)[1].lower()


def is_valid_file_type(filename: str, allowed_extensions: list = None) -> bool:
    """
    Check if file type is valid
    """
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.txt']
    
    extension = get_file_extension(filename)
    return extension in allowed_extensions


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in MB
    """
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)


def validate_file_size(file_path: str, max_size_mb: int = 10) -> bool:
    """
    Validate if file size is within limit
    """
    size_mb = get_file_size_mb(file_path)
    return size_mb <= max_size_mb


def generate_file_hash(file_path: str) -> str:
    """
    Generate MD5 hash of file for duplicate detection
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def format_timestamp(dt: datetime = None) -> str:
    """
    Format datetime to string
    """
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def sanitize_filename(filename: str) -> str:
    """
    Remove special characters from filename
    """
    # Keep only alphanumeric, dots, hyphens, and underscores
    import re
    return re.sub(r'[^\w\-.]', '_', filename)


def extract_keywords(text: str, max_keywords: int = 5) -> list:
    """
    Extract keywords from text for video search
    """
    # Simple keyword extraction (you can use NLP libraries for better results)
    import re
    
    # Remove special characters
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Common stop words to ignore
    stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by'}
    
    # Split into words and filter
    words = [word for word in text.split() if word not in stop_words and len(word) > 3]
    
    # Count word frequency
    word_count = {}
    for word in words:
        word_count[word] = word_count.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:max_keywords]]


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def is_image_file(filename: str) -> bool:
    """
    Check if file is an image
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
    return get_file_extension(filename) in image_extensions


def is_pdf_file(filename: str) -> bool:
    """
    Check if file is a PDF
    """
    return get_file_extension(filename) == '.pdf'


def is_document_file(filename: str) -> bool:
    """
    Check if file is a document (DOCX, TXT)
    """
    doc_extensions = ['.docx', '.txt', '.doc']
    return get_file_extension(filename) in doc_extensions


def create_error_response(error_message: str, error_code: str = "ERROR") -> dict:
    """
    Create standardized error response
    """
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": error_message,
            "timestamp": format_timestamp()
        }
    }


def create_success_response(data: dict, message: str = "Success") -> dict:
    """
    Create standardized success response
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": format_timestamp()
    }


def clean_text(text: str) -> str:
    """
    Clean and normalize text
    """
    import re
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    return text.strip()


def extract_subject_from_text(text: str) -> Optional[str]:
    """
    Try to extract subject from assignment text
    """
    # Common subjects
    subjects = [
        'mathematics', 'math', 'algebra', 'geometry', 'calculus',
        'physics', 'chemistry', 'biology', 'science',
        'english', 'literature', 'grammar', 'writing',
        'history', 'geography', 'social studies',
        'computer science', 'programming', 'coding'
    ]
    
    text_lower = text.lower()
    
    for subject in subjects:
        if subject in text_lower:
            return subject.title()
    
    return None


def page_content_summary(content: str, max_words: int = 50) -> str:
    """
    Create a summary of page content
    """
    words = content.split()
    if len(words) <= max_words:
        return content
    
    summary = ' '.join(words[:max_words])
    return summary + "..."


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Calculate estimated reading time in minutes
    """
    word_count = len(text.split())
    minutes = word_count / words_per_minute
    return max(1, round(minutes))


def detect_question_type(question: str) -> str:
    """
    Detect type of question being asked
    """
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['how to', 'how do', 'how can']):
        return "how-to"
    elif any(word in question_lower for word in ['what is', 'what are', 'define']):
        return "definition"
    elif any(word in question_lower for word in ['why', 'explain', 'reason']):
        return "explanation"
    elif any(word in question_lower for word in ['solve', 'calculate', 'compute']):
        return "problem-solving"
    elif any(word in question_lower for word in ['compare', 'difference', 'versus']):
        return "comparison"
    else:
        return "general"


def validate_interaction_type(interaction_type: str) -> bool:
    """
    Validate if interaction_type is valid for chatbot
    """
    valid_types = ['greeting', 'ai_response', 'user_question']
    return interaction_type in valid_types


def format_chatbot_response(response: str) -> str:
    """
    Format AI response for better readability
    - Ensure proper spacing
    - Maintain bullet points and numbered lists
    - Remove excessive blank lines
    """
    import re
    
    # Remove multiple blank lines
    response = re.sub(r'\n\n+', '\n\n', response)
    
    # Ensure proper spacing around bullet points
    response = re.sub(r'\n\s*[-•*]\s*', '\n• ', response)
    
    # Ensure proper spacing around numbered lists
    response = re.sub(r'\n\s*(\d+)\.\s*', r'\n\1. ', response)
    
    return response.strip()


def extract_ai_topic_from_response(response: str) -> Optional[str]:
    """
    Extract main topic/subject from AI response
    Useful for follow-up questions
    """
    # Get first sentence or first line as topic
    lines = response.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 10:
            # Remove markdown formatting
            import re
            clean_line = re.sub(r'[*_#]', '', line)
            return clean_line[:80]  # Return first 80 chars
    
    return None


def check_if_asking_for_solution(question: str) -> bool:
    """
    Check if student is explicitly asking for full solution
    """
    solution_keywords = [
        'full solution', 'complete solution', 'full answer',
        'solve it', 'solve this', 'show me the answer',
        'just tell me', 'i give up', 'give up',
        'show me how', 'step by step solution'
    ]
    
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in solution_keywords)


def check_if_asking_for_clarification(question: str) -> bool:
    """
    Check if student is asking for clarification/explanation
    """
    clarification_keywords = [
        'explain', 'clarify', 'clear', 'confused',
        'understand', 'different way', 'simpler',
        'again', 'more detail', 'example',
        'what do you mean', 'can you break it down'
    ]
    
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in clarification_keywords)


def check_if_follow_up_question(question: str) -> bool:
    """
    Check if this is a follow-up to previous response
    """
    followup_patterns = [
        'and ', 'but ', 'what about', 'how about',
        'also ', 'then ', 'next ', 'another',
        'after that', 'then what', 'what else'
    ]
    
    question_lower = question.lower()
    return any(pattern in question_lower for pattern in followup_patterns)


def format_conversation_history(messages: list, max_display: int = 10) -> str:
    """
    Format conversation history for logging/debugging
    """
    conversation_text = ""
    
    # Show last max_display messages
    recent_messages = messages[-max_display:] if len(messages) > max_display else messages
    
    for i, msg in enumerate(recent_messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        
        # Truncate long messages for readability
        if len(content) > 150:
            content = content[:150] + "..."
        
        conversation_text += f"\n{i}. {role.upper()}: {content}"
    
    return conversation_text


def estimate_response_level(conversation_history: list) -> str:
    """
    Estimate what level of explanation student needs based on conversation history
    Returns: 'beginner', 'intermediate', or 'advanced'
    """
    if not conversation_history:
        return 'beginner'
    
    # Count question types in history
    clarification_count = 0
    solution_requests = 0
    
    for msg in conversation_history:
        if msg.get('role') == 'user':
            content = msg.get('content', '')
            if check_if_asking_for_clarification(content):
                clarification_count += 1
            if check_if_asking_for_solution(content):
                solution_requests += 1
    
    # If many clarifications needed, student is beginner
    if clarification_count > 2:
        return 'beginner'
    
    # If requesting solutions, probably stuck
    if solution_requests > 0:
        return 'intermediate'
    
    # If asking follow-ups, probably advanced
    if len(conversation_history) > 4:
        return 'advanced'
    
    return 'beginner'