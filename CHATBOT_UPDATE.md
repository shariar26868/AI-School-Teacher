# Enhanced Chatbot: Two-Option System

## Overview
The chatbot has been updated to support a **two-option interactive system** where students can:
1. **Get AI responses** to their assignment questions
2. **Continue conversations** based on AI responses

## Architecture Changes

### 1. Updated Route Model (`app/routes/chatbot.py`)

#### New Request Schema:
```python
class QuestionRequest(BaseModel):
    assignment_id: str
    student_id: str
    question: str
    interaction_type: Literal["greeting", "ai_response", "user_question"] = "ai_response"
    previous_ai_response: Optional[str] = None
```

#### New Response Schema:
```python
class ChatResponse(BaseModel):
    answer: str
    video_links: list = []
    assignment_title: str
    should_show_videos: bool = False
    interaction_type: str = "ai_response"
```

### 2. Three Interaction Types

#### A. Greeting Mode (`interaction_type="greeting"`)
- Initial greeting message with instructions
- Explains the two available options
- Displayed when student first starts the conversation

**Request Example:**
```json
{
  "assignment_id": "123",
  "student_id": "456",
  "question": "Hi",
  "interaction_type": "greeting"
}
```

#### B. AI Response Mode (`interaction_type="ai_response"`)
- Students ask a question about the assignment
- AI provides hints/guidance first (not full solution)
- Full solution only when explicitly requested
- YouTube videos suggested after full solution

**Request Example:**
```json
{
  "assignment_id": "123",
  "student_id": "456",
  "question": "How do I calculate the area of a triangle?",
  "interaction_type": "ai_response"
}
```

#### C. User Continuation Mode (`interaction_type="user_question"`)
- Students ask follow-up questions after AI response
- Previous AI response is passed for context
- Allows natural back-and-forth conversation
- Can request different explanations or go deeper

**Request Example:**
```json
{
  "assignment_id": "123",
  "student_id": "456",
  "question": "Can you explain this step differently?",
  "interaction_type": "user_question",
  "previous_ai_response": "The area formula is: Area = (1/2) × base × height..."
}
```

## New Service Functions (`app/services/chatbot_service.py`)

### 1. `get_greeting_response(assignment_title: str) -> str`
- Returns the initial greeting message
- Explains both interaction options to the student
- Makes the two-option system clear from the start

### 2. `handle_ai_response(...) -> str`
- Processes student questions
- Retrieves conversation history
- Generates AI response using GPT-4o
- Implements teaching rules (hints first, solutions only when asked)
- Saves conversation to history

### 3. `handle_user_continuation(...) -> str`
- Handles follow-up questions from students
- Uses previous AI response as context
- Builds upon previous explanations
- Allows for natural conversation flow
- Adapts teaching style based on student needs

## Conversation Flow

```
1. Student initiates → interaction_type="greeting"
   ↓
2. AI sends greeting with options
   ↓
3. Student asks question → interaction_type="ai_response"
   ↓
4. AI provides hints/guidance
   ↓
5. Student asks follow-up → interaction_type="user_question"
   ↓
6. AI continues conversation
   ↓
7. Repeat steps 5-6 for more questions
```

## Key Features

### Greeting System
- Initial greeting message when student starts
- Clear explanation of both options
- Warm, welcoming tone

### Progressive Disclosure
- **First time:** Hints and guidance only
- **Follow-ups:** More detailed explanations
- **On request:** Full solution with step-by-step breakdown

### Conversation Continuity
- Maintains conversation history for each student-assignment pair
- Keeps last 20 messages to manage memory
- Passes previous AI response for context-aware responses

### Teaching Strategies
- Hints → Guidance → Partial Solutions → Full Solutions
- Adapts explanation style based on student feedback
- Encourages learning through guided discovery

## API Usage Examples

### 1. Initial Greeting
```bash
curl -X POST "http://localhost:8000/api/chatbot/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "assignment_id": "123",
    "student_id": "456",
    "question": "Hello",
    "interaction_type": "greeting"
  }'
```

### 2. Ask AI a Question
```bash
curl -X POST "http://localhost:8000/api/chatbot/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "assignment_id": "123",
    "student_id": "456",
    "question": "What is the formula for the area of a circle?",
    "interaction_type": "ai_response"
  }'
```

### 3. Follow-up User Question
```bash
curl -X POST "http://localhost:8000/api/chatbot/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "assignment_id": "123",
    "student_id": "456",
    "question": "Can you explain why we use π in that formula?",
    "interaction_type": "user_question",
    "previous_ai_response": "Area of circle = π × r² where r is the radius..."
  }'
```

## Frontend Integration

### Step 1: Initial Load
- Show greeting button or auto-trigger greeting
- Display greeting message with options

### Step 2: Question Input Mode
- Provide input field for "Ask AI a Question"
- Set `interaction_type="ai_response"`

### Step 3: Conversation Mode
- After AI response, show follow-up input
- Set `interaction_type="user_question"`
- Pass `previous_ai_response` in the request

## Changes Summary

| File | Changes |
|------|---------|
| `app/routes/chatbot.py` | Added `interaction_type` and `previous_ai_response` fields; implemented logic for greeting, ai_response, and user_question modes |
| `app/services/chatbot_service.py` | Added 3 new functions: `get_greeting_response()`, `handle_ai_response()`, `handle_user_continuation()` |
| `requirements.txt` | No changes needed (all dependencies already present) |

## Testing the System

1. **Test Greeting:**
   ```bash
   interaction_type = "greeting"
   question = "Hi"
   ```

2. **Test AI Response:**
   ```bash
   interaction_type = "ai_response"
   question = "What is a quadratic equation?"
   ```

3. **Test User Continuation:**
   ```bash
   interaction_type = "user_question"
   question = "Can you give an example?"
   previous_ai_response = <AI's previous response>
   ```

## Notes

- Conversation history is stored in-memory (last 20 messages per student-assignment pair)
- For production, consider using a database for conversation persistence
- YouTube video suggestions still trigger after full solutions
- All math equations are formatted in plain text (no LaTeX)
