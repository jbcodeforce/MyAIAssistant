# MyAIAssistant: Intelligent Todo and Knowledge Management

## Project Overview

MyAIAssistant is designed to be a comprehensive personal productivity and knowledge management tool. It integrates traditional task management (Todos) with an intelligent knowledge base, enabling users to efficiently organize tasks, reference subject-matter knowledge, and leverage AI for semantic search, note summarization, and task extraction. The tool helps linking knowledge to task to better address the work.

It is based on the 7 habits of effective people, manage the golden eggs and prioritize work efficiently.

## Key Features

1. [x] Kanban-style Todo Management user interface: Todos categorized by Importance/Urgency (Eisenhower Matrix).
1. Knowledge Base: Metadata centralized storage to reference existing documents, notes, and website links.
1. Semantic Search (RAG): AI-powered search across the knowledge base.
1. Task/Note Integration: Ability to automatically link Todos directly to relevant knowledge artifacts or meeting notes.
1. LLM Support: Automated extraction of action items (Todos) from meeting notes/transcripts. Automatic link between to do and knowledge. Ollama or other efficient local model execution.  
1. Run locally only.
1. External configuration.

## Technical Stack

| Layer | Technology | Purpose | Notes |
| ----- | ---------- | ------- | ----- |
| Frontend | Vue.js (using Vite) | User Interface and state management. | Focus on responsive canvas and drag-and-drop for Todo visualization. |
| Backend API | Python FastAPI | asynchronous API for logic and data orchestration. | Handles all data persistence, AI calls, and business logic. |
| Relational Database | PostgreSQL/SQLite | Structured data persistence. | Storing Todos, their states, user settings, knowledge metadata, and subject relationships. |
| Vector Database| ChromaDB, Pinecone, Qdrant | Semantic Search and Retrieval-Augmented Generation (RAG).| Stores text embeddings of all knowledge content (notes, documents, websites).|
| LLM Integration| OpenAI SDK | Core AI services. | Used for semantic search, knowledge extraction, summarization, and task generation.| 
