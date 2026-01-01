from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import assignments, chatbot
from app.services.db_service import connect_db, close_db
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs("temp", exist_ok=True)
    await connect_db()
    print("✅ Database connected")
    print("✅ Temp folder created")
    yield
    # Shutdown
    await close_db()
    print("❌ Database disconnected")

app = FastAPI(
    title="AI Assignment Helper",
    description="Backend API for student assignment assistance with AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS with increased timeout for large file uploads
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(assignments.router, prefix="/api", tags=["Assignments"])
app.include_router(chatbot.router, prefix="/api", tags=["Chatbot"])

@app.get("/")
async def root():
    return {
        "message": "AI Assignment Helper API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Run with: uvicorn main:app --reload --timeout-keep-alive 300 --limit-concurrency 1000