from typing import Dict, List, Optional, Any, Type
from fastapi import Depends, UploadFile, HTTPException
import fitz
from hashlib import sha256
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import numpy as np
import uuid
import re
from typing import List
import re
from app.core.database import get_db, get_qdrant
from app.core.config import Settings
from app.models.document import Document, TextChunk

settings = Settings()



def recursive_split_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    chunks = []
    separators = ["\n\n", "\n", ".", " "]
    
    def split_by_separator(text: str, separators: List[str]) -> List[str]:
        if not separators:
            return [text]
            
        separator = separators[0]
        splits = text.split(separator)
        
        if len(splits) == 1:
            return split_by_separator(text, separators[1:])
            
        results = []
        current_chunk = ""
        
        for split in splits:
            if not split:
                continue
                
            potential_chunk = current_chunk + (separator if current_chunk else "") + split
            
            if len(potential_chunk) > chunk_size:
                if current_chunk:
                    results.extend(split_by_separator(current_chunk, separators[1:]))
                results.extend(split_by_separator(split, separators[1:]))
                current_chunk = ""
            else:
                current_chunk = potential_chunk
                
        if current_chunk:
            results.extend(split_by_separator(current_chunk, separators[1:]))
            
        return results
    
    raw_chunks = split_by_separator(text, separators)
    
    for i, chunk in enumerate(raw_chunks):
        chunks.append(chunk)
        
        if i < len(raw_chunks) - 1 and chunk_overlap > 0:
            next_chunk = raw_chunks[i + 1]
            if len(next_chunk) > chunk_overlap:
                overlap = next_chunk[:chunk_overlap]
                chunks[-1] = chunks[-1] + "\n" + overlap
                
    return chunks



def sentence_split_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    # Split text into sentences using regex
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        if current_size + sentence_size > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            
            # Add overlap
            overlap_chunk = []
            overlap_size = 0
            for prev_sentence in reversed(current_chunk[-3:]):  # last 3 sentences as overlap
                if overlap_size + len(prev_sentence) <= chunk_overlap:
                    overlap_chunk.insert(0, prev_sentence)
                    overlap_size += len(prev_sentence)
                else:
                    break
            current_chunk = overlap_chunk
            current_size = sum(len(s) for s in current_chunk)
        
        current_chunk.append(sentence)
        current_size += sentence_size
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks



settings = Settings()

class DocumentService:
    def __init__(
        self,
        db: Session = Depends(get_db),
        qdrant: QdrantClient = Depends(get_qdrant)
    ):
        self.db = db
        self.qdrant = qdrant
        self.model = SentenceTransformer(settings.embedding_model)

    async def process_file(
        self,
        file: UploadFile,
        chunking_strategy: str = "recursive",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Document:
        
        file_content = await file.read()
        file_hash = sha256(file_content).hexdigest()

        existing_doc = self.db.query(Document).filter(Document.content_hash == file_hash).first()
        if existing_doc:
            return existing_doc

        text = ""
        if file.filename.endswith(".pdf"):
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page in doc:
                text += page.get_text()
        elif file.filename.endswith(".txt"):
            text = file_content.decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        document = Document(
            filename=file.filename,
            content_hash=file_hash,
            chunking_strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            doc_metadata ={
                "original_filename": file.filename,
                "file_size": len(file_content),
                "chunking_strategy": chunking_strategy,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap
            }
        )
        self.db.add(document)
        self.db.commit()

        chunks = []
        if chunking_strategy == "recursive":
            chunks = recursive_split_text(text, chunk_size, chunk_overlap)
        elif chunking_strategy == "sentence":
            chunks = sentence_split_text(text, chunk_size, chunk_overlap)
        else:
            raise HTTPException(status_code=400, detail="Invalid chunking strategy")

        for i, chunk_text in enumerate(chunks):
            embedding = self.model.encode([chunk_text])[0]
            
            vector_id = str(uuid.uuid4())
            
            self.qdrant.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=[PointStruct(
                    id=vector_id,
                    vector=embedding.tolist(),
                    payload={"text": chunk_text, "doc_id": document.id}
                )]
            )
            
            chunk = TextChunk(
                document_id=document.id,
                chunk_index=i,
                content=chunk_text,
                vector_id=vector_id,
                chunk_metadata={
                    "document_id": document.id,
                    "chunk_index": i,
                    "vector_id": vector_id,
                    "chunk_size": document.chunk_size,
                    "chunk_overlap": document.chunk_overlap,
                    "strategy": document.chunking_strategy
                }
            )
            self.db.add(chunk)
        
        self.db.commit()
        return document

  
