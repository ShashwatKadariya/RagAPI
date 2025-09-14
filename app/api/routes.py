from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
import uuid
from sqlalchemy.orm import Session
from app.services.document_service import DocumentService
from app.services.chat_service import ChatService
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import DocumentResponse
from app.core.database import get_db
from app.models.document import Document, TextChunk
from fastapi import Query

from app.schemas.document import ChunkingStrategy


document_router = APIRouter()
chat_router = APIRouter()


@document_router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunking_strategy: ChunkingStrategy = Query(
        default=ChunkingStrategy.RECURSIVE,
        description="Chunking strategy to use: 'recursive' or 'sentence'"
    ),
    doc_service: DocumentService = Depends()
):

    if file.filename.endswith(('.pdf', '.txt')):
        try:
            doc_id = await doc_service.process_file(file, chunking_strategy)
            return {
                "document_id": str(doc_id),
                "filename": file.filename,
                "chunking_strategy": chunking_strategy
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

@chat_router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    chat_service: ChatService = Depends()
):

    try:
        # Generate or use existing conversation ID
        conv_id = request.conversation_id or str(uuid.uuid4())
        
        # Get response using RAG
        response = await chat_service.get_response(
            query=request.query,
            conversation_id=conv_id
        )
        
        return {
            "answer": response["answer"],
            "sources": response["sources"],
            "conversation_id": conv_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
