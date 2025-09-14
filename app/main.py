from fastapi import FastAPI
from app.api.routes import document_router, chat_router
from app.api.booking import booking_router
from app.core.init_db import init_db

app = FastAPI(
    title="RAG API",
    description="REST API for document ingestion, conversational RAG, and interview bookings",
    version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    init_db()

app.include_router(document_router, prefix="/api/documents", tags=["documents"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Welcome to RAG API"}
