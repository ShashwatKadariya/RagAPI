from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    content_hash = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    doc_metadata = Column(JSON)

    chunking_strategy = Column(String, nullable=True)
    chunk_size = Column(Integer, nullable=True)
    chunk_overlap = Column(Integer, nullable=True)

class TextChunk(Base):
    __tablename__ = "text_chunks"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer)
    chunk_index = Column(Integer)
    content = Column(Text)
    vector_id = Column(String)  # ID in Qdrant
    created_at = Column(DateTime, default=datetime.utcnow)
    chunk_metadata = Column(JSON)
