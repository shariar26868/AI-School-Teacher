from openai import OpenAI
from app.config import settings
from typing import List, Dict, Optional
import re
from datetime import datetime
from app.services import db_service

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def get_conversation_history(student_id: str, assignment_id: str) -> List[Dict]:
    """Get conversation history for a student-assignment pair from database"""
    try:
        if db_service.database is None:
            return []
        
        chat_collection = db_service.database.get_collection('chat_messages')
        
        messages = await chat_collection.find({
            "student_id": student_id,
            "assignment_id": assignment_id
        }).to_list(length=None)
        
        # Sort by creation time
        messages = sorted(messages, key=lambda x: x.get('created_at', datetime.utcnow()))
        
        # Keep only last 20 messages
        if len(messages) > 20:
            messages = messages[-20:]
        
        # Remove MongoDB _id field
        for msg in messages:
            msg.pop('_id', None)
            msg.pop('created_at', None)
        
        return messages
        
    except Exception as e:
        print(f"Error retrieving conversation history: {e}")
        return []


async def save_conversation(student_id: str, assignment_id: str, role: str, content: str, interaction_type: str = "ai_response"):
    """Save a message to conversation history in database"""
    try:
        if db_service.database is None:
            return
        
        chat_collection = db_service.database.get_collection('chat_messages')
        
        message_doc = {
            "student_id": student_id,
            "assignment_id": assignment_id,
            "role": role,
            "content": content,
            "interaction_type": interaction_type,
            "created_at": datetime.utcnow()
        }
        
        await chat_collection.insert_one(message_doc)
        
    except Exception as e:
        print(f"Error saving conversation: {e}")


async def clear_conversation(student_id: str, assignment_id: str):
    """Clear conversation history from database"""
    try:
        if db_service.database is None:
            return
        
        chat_collection = db_service.database.get_collection('chat_messages')
        
        await chat_collection.delete_many({
            "student_id": student_id,
            "assignment_id": assignment_id
        })
        
    except Exception as e:
        print(f"Error clearing conversation: {e}")


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
    history = await get_conversation_history(student_id, assignment_id)
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
        
        await save_conversation(student_id, assignment_id, "user", question)
        await save_conversation(student_id, assignment_id, "assistant", greeting_response)
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
    
    # Save to database
    await save_conversation(student_id, assignment_id, "user", question)
    await save_conversation(student_id, assignment_id, "assistant", answer)
    
    return answer


async def should_suggest_videos(question: str, answer: str, history: List[Dict]) -> bool:
    """
    Decide if we should suggest YouTube videos
    Now suggests videos for any detailed response to help reinforce learning
    """
    # Don't suggest for greetings
    if is_greeting(question):
        return False
    
    # Always suggest unless it's a very short response
    answer_lower = answer.lower()
    
    # Check if answer is substantial enough (at least 200 characters)
    is_substantial = len(answer) > 200
    
    # Check if it looks like actual content (not just greeting or placeholder)
    has_content = any(indicator in answer_lower for indicator in [
        'step', 'example', 'formula', 'equation', 'answer', 'solution',
        'therefore', 'however', 'also', 'this', 'that', 'the',
        'is', 'are', 'explain', 'understand', 'learn', 'help'
    ])
    
    # Decision: suggest videos for substantial, content-rich responses
    should_suggest = is_substantial and has_content
    
    print(f"\n📺 Video Suggestion Analysis:")
    print(f"   - Is substantial (>200 chars): {is_substantial} (length: {len(answer)})")
    print(f"   - Has content: {has_content}")
    print(f"   - 💡 Suggest videos: {should_suggest}")
    
    return should_suggest


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


def get_greeting_response(assignment_title: str) -> str:
    """
    Get greeting response for initial student interaction
    """
    greeting_response = f"""👋 Hello! Welcome to the AI Assignment Helper!

I'm here to help you with: **{assignment_title}**

You have two options:

**Option 1: Ask AI a Question** 🤖
- Ask me anything about the assignment
- I'll give you hints and guidance first
- Ask again for more detailed explanations
- Request the full solution when you're stuck

**Option 2: Continue the Conversation** 💬
- After I respond to your question, you can ask follow-up questions
- I'll explain it differently if you don't understand
- We can go back and forth naturally

What would you like to do? Just ask me any question about the assignment!"""
    
    return greeting_response


async def handle_ai_response(
    question: str,
    assignment_context: str,
    assignment_title: str,
    student_id: str,
    assignment_id: str
) -> str:
    """
    Handle AI response mode: AI responds to student's question
    """
    
    # Get conversation history
    history = await get_conversation_history(student_id, assignment_id)
    is_first_message = len(history) == 0
    
    # Handle greetings
    if is_greeting(question) and len(question.split()) <= 3:
        response = get_greeting_response(assignment_title)
        await save_conversation(student_id, assignment_id, "user", question, "greeting")
        await save_conversation(student_id, assignment_id, "assistant", response, "greeting")
        return response
    
    # Build system prompt for AI response
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
    
    # Save to database
    await save_conversation(student_id, assignment_id, "user", question, "ai_response")
    await save_conversation(student_id, assignment_id, "assistant", answer, "ai_response")
    
    return answer


async def handle_user_continuation(
    user_input: str,
    previous_ai_response: str,
    assignment_context: str,
    assignment_title: str,
    student_id: str,
    assignment_id: str
) -> str:
    """
    Handle user continuation: Allow user to follow up on AI response
    """
    
    # Get conversation history
    history = await get_conversation_history(student_id, assignment_id)
    
    # Build system prompt for continuation
    system_content = f"""You are a friendly and helpful teacher assistant for students.

Assignment Title: {assignment_title}

Assignment Content:
{assignment_context}

PREVIOUS AI RESPONSE:
{previous_ai_response}

CONVERSATION STYLE:
- Be natural and conversational like ChatGPT
- Build upon the previous response
- Don't repeat what you already said
- Be more detailed if they ask for clarification
- Use simple, clear language
- NEVER use LaTeX formatting (\\[ \\], \\( \\), etc.)
- Write all math equations in plain text

TEACHING RULES FOR CONTINUATION:
1. **If asking for clarification**: Explain more simply, use different examples
2. **If asking about another part**: Smoothly transition to that topic
3. **If still confused**: Break down into smaller steps
4. **If asking for full solution**: Provide complete step-by-step solution
5. **If asking to continue**: Go deeper into the explanation

Remember the previous response and build upon it naturally. Don't restart the explanation."""

    # Build messages
    messages = [{"role": "system", "content": system_content}]
    
    # Add conversation history
    messages.extend(history)
    
    # Add user continuation input
    messages.append({"role": "user", "content": user_input})
    
    # Get response from GPT
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=1500
    )
    
    answer = response.choices[0].message.content
    
    # Save to database
    await save_conversation(student_id, assignment_id, "user", user_input, "user_question")
    await save_conversation(student_id, assignment_id, "assistant", answer, "user_question")
    
    return answer