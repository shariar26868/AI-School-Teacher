# AI Assignment Helper - Backend API

FastAPI backend for AI-powered student assignment assistance system.

## Features

- ✅ Upload assignments (PDF, images, DOCX, TXT)
- ✅ Multi-page document support
- ✅ OCR using GPT-4 Vision
- ✅ AI chatbot for answering student questions
- ✅ YouTube video recommendations
- ✅ AWS S3 storage
- ✅ MongoDB database

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your credentials

3. Run the server:
```bash
uvicorn main:app --reload
```

4. API Docs: http://localhost:8000/docs

## API Endpoints

### Assignments
- `POST /api/assignments/upload` - Upload assignment
- `GET /api/assignments` - List all assignments
- `GET /api/assignments/{id}` - Get specific assignment

### Chatbot
- `POST /api/chat` - Ask question about assignment

## Tech Stack

- FastAPI
- OpenAI GPT-4
- AWS S3
- MongoDB
- YouTube API