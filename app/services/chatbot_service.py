from openai import OpenAI
from app.config import settings
from typing import List, Dict, Optional
import re

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# In-memory conversation storage
conversations: Dict[str, List[Dict]] = {}


def get_conversation_history(student_id: str, assignment_id: str) -> List[Dict]:
    """Get conversation history for a student-assignment pair"""
    key = f"{student_id}_{assignment_id}"
    return conversations.get(key, [])


def save_conversation(student_id: str, assignment_id: str, role: str, content: str):
    """Save a message to conversation history"""
    key = f"{student_id}_{assignment_id}"
    
    if key not in conversations:
        conversations[key] = []
    
    conversations[key].append({
        "role": role,
        "content": content
    })
    
    # Keep only last 20 messages
    if len(conversations[key]) > 20:
        conversations[key] = conversations[key][-20:]


def clear_conversation(student_id: str, assignment_id: str):
    """Clear conversation history"""
    key = f"{student_id}_{assignment_id}"
    if key in conversations:
        del conversations[key]


def is_greeting(text: str) -> bool:
    """Check if message is a greeting"""
    greetings = [
        'hi', 'hello', 'hey', 'hola', 'greetings',
        'good morning', 'good afternoon', 'good evening',
        'whats up', "what's up", 'sup', 'yo',
        'assalamualaikum', 'salam'
    ]
    text_lower = text.lower().strip()
    return any(greeting in text_lower for greeting in greetings) and len(text.split()) <= 3


def is_asking_for_help(text: str) -> bool:
    """Check if student is asking what help is available"""
    help_phrases = [
        'help me', 'can you help', 'need help',
        'what can you do', 'how can you help',
        'what should i do', 'where do i start'
    ]
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in help_phrases)


def is_requesting_full_solution(text: str) -> bool:
    """Check if student explicitly wants full solution"""
    solution_requests = [
        'full solution', 'complete solution', 'full answer',
        'solve it for me', 'show me the solution',
        'give me the answer', 'just tell me', 'i give up',
        'show me how to solve', 'solve this', 'puro solve koro',
        'full solve', 'complete solve'
    ]
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in solution_requests)


def is_asking_specific_question(text: str) -> bool:
    """Check if asking about a specific question"""
    question_indicators = [
        'question', 'problem', 'solve', 'how do i', 'how to',
        'part a', 'part b', 'part c', 'part d',
        'q1', 'q2', 'q3', 'question 1', 'question 2'
    ]
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in question_indicators)


async def answer_question(
    question: str, 
    assignment_context: str, 
    assignment_title: str,
    student_id: str,
    assignment_id: str
) -> str:
    """
    Answer student question with natural conversation flow
    """
    
    # Get conversation history
    history = get_conversation_history(student_id, assignment_id)
    is_first_message = len(history) == 0
    
    # Handle greetings (first message or standalone greeting)
    if is_greeting(question) and len(question.split()) <= 3:
        greeting_response = """Hello! 👋 

I'm here to help you with your assignment. I can:
- Answer questions about any part of the assignment
- Give you hints and guidance to solve problems
- Explain concepts step by step
- Provide full solutions if you're really stuck

Which question would you like to start with? Just tell me the question number or describe what you need help with!"""
        
        save_conversation(student_id, assignment_id, "user", question)
        save_conversation(student_id, assignment_id, "assistant", greeting_response)
        return greeting_response
    
    # Build system prompt based on conversation stage
    system_content = f"""You are a friendly and helpful teacher assistant for students.

Assignment Title: {assignment_title}

Assignment Content:
{assignment_context}

CONVERSATION STYLE:
- Be natural and conversational like ChatGPT
- Don't be overly formal or robotic
- Use simple, clear language
- Be encouraging and supportive
- NEVER use LaTeX formatting (\\[ \\], \\( \\), etc.)
- Write all math equations in plain text (e.g., "Area = 1/2 × base × height" or "Area = (1/2) * base * height")
- Use regular text with symbols: ×, ÷, =, ², ³
- Format should be readable in plain text messages

TEACHING RULES:
1. **For greetings/general questions**: Greet warmly and ask which question they need help with

2. **For specific questions**: 
   - First time: Give HINTS and GUIDANCE only (not full solution)
   - Ask guiding questions
   - Provide similar examples
   - Encourage them to try
   
3. **If student asks for more help**:
   - Give more detailed hints
   - Break down steps
   - Show partial solutions
   
4. **ONLY give full solution when explicitly requested**:
   - "Give me the full solution"
   - "Solve it for me"
   - "I give up"
   - "Just show me the answer"

5. **Adapt your style**:
   - If they ask "explain differently" → use different approach
   - If confused → simplify your language
   - If stuck → give more hints

IMPORTANT: 
- Start with hints, NOT solutions
- Only escalate when student explicitly asks
- Remember previous conversation context
- Be patient and encouraging"""

    # Build messages
    messages = [{"role": "system", "content": system_content}]
    
    # Add conversation history
    messages.extend(history)
    
    # Add current question
    messages.append({"role": "user", "content": question})
    
    # Get response from GPT
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=1500
    )
    
    answer = response.choices[0].message.content
    
    # Save to history
    save_conversation(student_id, assignment_id, "user", question)
    save_conversation(student_id, assignment_id, "assistant", answer)
    
    return answer


async def should_suggest_videos(question: str, answer: str, history: List[Dict]) -> bool:
    """
    Decide if we should suggest YouTube videos
    Only suggest after full solution is given
    """
    # Don't suggest for greetings or initial questions
    if is_greeting(question):
        return False
    
    # Check if this was a request for full solution
    if is_requesting_full_solution(question):
        return True
    
    # More comprehensive solution detection
    answer_lower = answer.lower()
    
    # Check for mathematical calculations (LaTeX or plain)
    has_calculations = bool(
        re.search(r'\\[\[\(].*?=.*?\\[\]\)]', answer) or  # LaTeX math with =
        re.search(r'=\s*\d+', answer) or  # Simple equations like "= 60"
        re.search(r'\d+\s*(?:cm|m|km|kg|g|cm²|m²)', answer)  # Units
    )
    
    # Check for step-by-step solutions
    solution_indicators = [
        'step 1', 'step 2', 'step 3',
        'therefore', 'the answer is',
        'final answer', 'solution:',
        "here's the complete solution",
        'so, the', 'thus,', 'hence,',
        'let\'s plug', 'substitute',
        'we get', 'result is'
    ]
    
    has_solution_words = any(indicator in answer_lower for indicator in solution_indicators)
    
    # Check if answer is detailed enough
    is_detailed = len(answer) > 400  # Lowered threshold
    
    # Check if it contains actual numeric answer
    has_numeric_answer = bool(re.search(r'(?:answer|area|result).*?(?:is|=)\s*\d+', answer_lower))
    
    # Decision logic
    is_full_solution = (
        has_calculations and is_detailed and (has_solution_words or has_numeric_answer)
    )
    
    print(f"\n🔍 Video Detection Analysis:")
    print(f"   - Has calculations: {has_calculations}")
    print(f"   - Has solution words: {has_solution_words}")
    print(f"   - Is detailed (>400 chars): {is_detailed} (length: {len(answer)})")
    print(f"   - Has numeric answer: {has_numeric_answer}")
    print(f"   - 📺 Suggest videos: {is_full_solution}")
    
    return is_full_solution


async def search_youtube_videos(query: str, max_results: int = 3) -> List[Dict]:
    """Search YouTube for educational videos"""
    try:
        from googleapiclient.discovery import build
        
        youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
        
        search_response = youtube.search().list(
            q=query + " tutorial explained",
            type='video',
            part='id,snippet',
            maxResults=max_results,
            relevanceLanguage='en',
            safeSearch='strict',
            videoEmbeddable='true',
            order='relevance'
        ).execute()
        
        videos = []
        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            videos.append({
                'title': item['snippet']['title'],
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                'description': item['snippet']['description'][:150]
            })
        
        return videos
        
    except Exception as e:
        print(f"YouTube search error: {e}")
        return []


async def generate_search_query(question: str, answer: str, assignment_context: str) -> str:
    """Generate YouTube search query from the conversation"""
    
    # Extract key topics from question and answer
    prompt = f"""Based on this student question and answer, generate a SHORT YouTube search query (4-6 words max) 
that will find the best educational tutorial videos.

Question: {question}

Answer excerpt: {answer[:500]}

Return ONLY the search query, nothing else. Make it educational and tutorial-focused.

Examples:
- "algebra equations tutorial"
- "quadratic formula explained"
- "trigonometry basics tutorial"
- "area of triangle formula"
"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You generate concise YouTube search queries for educational content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=30
    )
    
    query = response.choices[0].message.content.strip().strip('"').strip("'")
    return query