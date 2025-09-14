from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from qdrant_client import QdrantClient
from qdrant_client.http.models.models import Distance, VectorParams
import redis
from app.core.config import Settings
from sentence_transformers import SentenceTransformer

settings = Settings()

# PostgreSQL
engine = create_engine(settings.postgres_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Qdrant
qdrant_client = QdrantClient(
    host=settings.qdrant_host,
    port=settings.qdrant_port,
    check_compatibility=False
)

# Initialize Qdrant collection
def init_qdrant():
    model = SentenceTransformer(settings.embedding_model)
    vector_size = model.get_sentence_embedding_dimension()
    
    collections = qdrant_client.get_collections().collections
    exists = any(collection.name == settings.QDRANT_COLLECTION for collection in collections)
    
    if not exists:
        qdrant_client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

# Redis
redis_client = redis.Redis.from_url(settings.redis_url)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_qdrant():
    return qdrant_client

def get_redis():
    return redis_client

def get_booking_service():
    from app.services.booking_service import BookingService
    return BookingService()