from datetime import datetime

from typing import Dict, List, Optional, Any
from fastapi import Depends
import redis
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import httpx
import json
from sqlalchemy.orm import Session
from app.schemas.booking import BookingCreate

from app.core.database import get_booking_service, get_redis, get_qdrant
from app.core.config import Settings
from app.core.database import get_db
from fastapi import Depends
from app.models.booking import Booking



settings = Settings()

class ChatService:
    def __init__(
        self,
        redis_client: redis.Redis = Depends(get_redis),
        qdrant: QdrantClient = Depends(get_qdrant),
        db: Session = Depends(get_db),
    ):
        self.redis = redis_client
        self.qdrant = qdrant
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.ollama_url = f"{settings.ollama_host}/api/generate"
        self.db = db

    def _get_relevant_chunks(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_vector = self.embedding_model.encode([query])[0].tolist()
        
        results = self.qdrant.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=top_k
        )
        
        return results

    async def get_response(
        self,
        query: str,
        conversation_id: str,
        max_history: int = 5,
    ) -> Dict[str, Any]:
        
        self._store_chat_message(conversation_id, "user", query)

        booking_keywords = ["book interview", "schedule interview", "interview booking", "book an interview", "schedule an interview", "interview appointment", "interview"]

        # Check if booking flow should be triggered
        if any(kw in query.lower() for kw in booking_keywords) or self.redis.exists(f"booking:{conversation_id}"):            
            return await self._handle_booking_flow(conversation_id, query)


        history = self._get_chat_history(conversation_id, max_history)
        print("Chat history:", history, 'for conversation_id:', conversation_id, 'query:', query)

        relevant_chunks = self._get_relevant_chunks(query)

        messages = [
            {"role": "system", "content": (
                "You are a helpful assistant with access to a document database. "
                "Use the provided context to answer questions accurately and cite your sources. "
                "If you're unsure or the context doesn't contain the information, say so. "
                "Maintain conversation context for follow-up questions."
            )}
        ]

        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        context = "\n\n".join([chunk.payload["text"] for chunk in relevant_chunks])
        if not context.strip():
            context = "No relevant context available."
        messages.append({
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}"
        })

        prompt = "\n".join([msg["content"] for msg in messages])
        print(f"Prompt length: {len(prompt)}")
        
        async with httpx.AsyncClient(timeout=120) as client: 
            try:
                response = await client.post(
                    self.ollama_url,
                    json={
                        "model": settings.ollama_model,
                        "prompt": prompt,
                    }
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                print("Ollama API error:", e)
                return {"answer": "Error generating response", "sources": []}

        answer = ""
        lines = response.text.strip().splitlines()
        for line in lines:
            try:
                data = json.loads(line)
                answer += data.get("response", "")
            except json.JSONDecodeError:
                print("Skipping malformed line from Ollama:", line)

        print("Ollama response:", answer)

        self._store_chat_message(conversation_id, "assistant", answer)

        return {
            "answer": answer,
            "sources": [
                {
                    "content": chunk.payload["text"],
                    "score": chunk.score,
                    "metadata": {"doc_id": chunk.payload["doc_id"]}
                }
                for chunk in relevant_chunks
            ]
        }

    
    def _get_chat_history(self, conversation_id: str, max_history: int) -> List[Dict[str, str]]:
        """Get chat history from Redis"""
        history_key = f"chat:history:{conversation_id}"
        history = self.redis.lrange(history_key, 0, max_history * 2 - 1)  # *2 for pairs of messages
        
        if not history:
            return []
            
        return [json.loads(msg) for msg in history]
    
    def _store_chat_message(self, conversation_id: str, role: str, content: str):
        """Store chat message in Redis"""
        history_key = f"chat:history:{conversation_id}"
        message = json.dumps({"role": role, "content": content})
        
        self.redis.lpush(history_key, message)
        self.redis.expire(history_key, settings.chat_history_ttl)




    # TODO: ADD VALIDATION TO THE FIELDS BEFORE STORING THEM, IMPLEMENT BATCH INPUT(CURRENTLY ONLY SERIEAL INPUT)
    async def _handle_booking_flow(self, conversation_id: str, query: str) -> Dict[str, Any]:
        BOOKING_FIELDS = ["name", "email", "date", "time"]
        booking_key = f"booking:{conversation_id}"
        booking_state = self.redis.get(booking_key)

        if not booking_state:
            booking_state = {field: None for field in BOOKING_FIELDS}
            booking_state["step"] = "name"
            self.redis.set(booking_key, json.dumps(booking_state), ex=3600)
            return {"answer": "Sure, let's schedule an interview. Please provide your name.", "sources": []}

        booking_state = json.loads(booking_state)
        current_step = booking_state["step"]

        if current_step and current_step in BOOKING_FIELDS:
            booking_state[current_step] = query.strip()

        next_step = None
        for field in BOOKING_FIELDS:
            if not booking_state[field]:
                next_step = field
                break

        if next_step:
            booking_state["step"] = next_step
            self.redis.set(booking_key, json.dumps(booking_state), ex=3600)
            return {"answer": f"Please provide your {next_step} for booking.", "sources": []}
        else:
            booking_state["step"] = "complete"
            self.redis.delete(booking_key)

            db_booking = Booking(
                name=booking_state["name"],
                email=booking_state["email"],
                date=booking_state["date"],
                time=booking_state["time"],
            )

            self.db.add(db_booking)
            self.db.commit()
            self.db.refresh(db_booking)

            return {"answer": "✅ Your interview has been booked successfully!", "sources": []}
