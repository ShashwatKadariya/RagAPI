from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    postgres_url: str = "postgresql://postgres:postgres@postgres:5432/ragdb"
    
    # Qdrant
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    QDRANT_COLLECTION: str = "documents"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    chat_history_ttl: int = 3600  # 1 hour
    
    # Ollama
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "mistral:latest"
    
    # Embedding
    embedding_model: str = "all-mpnet-base-v2"
    
    # Text Processing
    chunk_size: int = 1500
    chunk_overlap: int = 150
    
    class Config:
        env_file = ".env"
