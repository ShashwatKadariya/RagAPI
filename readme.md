# Conversational RAG Backend with Document Ingestion and Interview Booking
(note: Mistral LLM is used for Chat System)

This project is a **backend system** built with **FastAPI** providing two main REST APIs:

1. **Document Ingestion API** – For uploading documents, processing them into embeddings, and storing metadata.
2. **Conversational RAG API** – For multi-turn conversations with retrieval-augmented generation (RAG) and interview booking functionality.

---

## Features

#### Completely Dockerized

**To Run** - docker compose up -d --build

**Swagger Docs** -localhost:8000/docs

### 1. Document Ingestion API

- Upload `.pdf` or `.txt` files.
- Extract text from documents.
- Apply **two selectable chunking strategies** (Recursive-Split and sentence-split).
- Generate embeddings using **sentence-transformers**(EMBEDDING_MODEL=all-mpnet-base-v2).
- Store embeddings in **Qdrants**.
- Save document metadata in **PostgreSQL**.

### 2. Conversational RAG API

- Custom RAG implementation (**no RetrievalQAChain used**).
- Redis-based chat memory for **multi-turn queries**.
- Handle **conversation context** efficiently.
- Interview booking flow with fields:
  - `name`
  - `email`
  - `date`
  - `time`
- Persist booking information in the backend database.

---

## Architecture

### DOCUMENT INGESTION API

1. Text Extraction
2. Chunking (Selectable, One of Two)
3. Embeddings -> VectorDB(Qdrant)
4. MetaData -> PostGreSQL

### Conversational RAG API

1. Chat Memory (Redis)
2. Query -> Embeddings -> Vector DB -> Retrieve
3. Custom RAG logic (merge context)
4. Response Generation
5. Interview Booking Flow
