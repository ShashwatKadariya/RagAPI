from enum import Enum
from pydantic import BaseModel

class ChunkingStrategy(str, Enum):
    RECURSIVE = "recursive"
    SENTENCE = "sentence"

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    chunking_strategy: ChunkingStrategy
