from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class Source(BaseModel):
    content: str
    score: float
    metadata: Dict[str, Any]

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    conversation_id: str
