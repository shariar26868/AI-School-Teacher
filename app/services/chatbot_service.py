from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def answer_question(question: str, assignment_context: str, assignment_title: str) -> str:
    """
    Answer student question using GPT-4
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a helpful and patient teacher assistant. Your job is to:
                1. Help students understand their assignment questions
                2. Provide step-by-step explanations
                3. Encourage learning rather than just giving answers
                4. Be supportive and motivating
                5. If a question is unclear, ask for clarification"""
            },
            {
                "role": "user",
                "content": f"""Assignment: {assignment_title}
                
Assignment Content:
{assignment_context}

Student Question: {question}

Please help the student understand this question and guide them toward the solution."""
            }
        ],
        temperature=0.7,
        max_tokens=1500
    )
    
    return response.choices[0].message.content