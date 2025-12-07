# Chat (Planned)

The chat component will provide an LLM-powered conversational interface for intelligent interactions with the knowledge base and task system.

## Planned Features

### Action Item Extraction

Extract tasks from meeting notes and transcripts:

```
Input: "In today's meeting, John agreed to review the API documentation
by Friday, and Sarah will update the deployment scripts."

Output:
- Todo: "Review API documentation" (assigned context: John, due: Friday)
- Todo: "Update deployment scripts" (assigned context: Sarah)
```

### Knowledge-Task Linking

Automatic suggestions linking todos to relevant knowledge items:

```
Todo: "Implement authentication middleware"
Suggested Knowledge:
- Authentication Guide (score: 0.92)
- Security Best Practices (score: 0.87)
- API Design Patterns (score: 0.71)
```

### Conversational Search

Natural language queries against the knowledge base:

```
User: "What's our approach to database migrations?"
Assistant: Based on the Engineering docs, migrations follow these steps:
1. Create migration script in /migrations
2. Test locally with `migrate test`
3. Apply in staging before production
[Source: Database Operations Guide, chunk 3]
```

## Planned Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Chat Interface                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Conversation History                    │   │
│  │  ┌──────┐  ┌────────────────────────────────────┐   │   │
│  │  │ User │  │ How do I configure the database?   │   │   │
│  │  └──────┘  └────────────────────────────────────┘   │   │
│  │  ┌──────┐  ┌────────────────────────────────────┐   │   │
│  │  │ Bot  │  │ Based on the config guide...       │   │   │
│  │  └──────┘  └────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Message Input                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Chat Service                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Context   │  │    RAG      │  │      LLM API        │ │
│  │  Assembly   │  │  Retrieval  │  │  (Ollama/OpenAI)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## LLM Provider Options

### Ollama (Local)

Run models locally for privacy:

```yaml
# Planned configuration
chat:
  provider: ollama
  model: llama2
  base_url: http://localhost:11434
```

Advantages:

- Complete privacy (no data leaves machine)
- No API costs
- Works offline

### OpenAI API

Cloud-based for higher capability:

```yaml
chat:
  provider: openai
  model: gpt-4
  api_key: ${OPENAI_API_KEY}
```

Advantages:

- More capable models
- No local compute requirements
- Faster responses

## Planned API Endpoints

### Send Message

```bash
POST /api/v1/chat/message
Content-Type: application/json

{
  "conversation_id": "uuid",
  "message": "What security practices should I follow?",
  "include_sources": true
}
```

### Extract Tasks

```bash
POST /api/v1/chat/extract-tasks
Content-Type: application/json

{
  "text": "Meeting notes content...",
  "auto_create": false
}
```

### Get Suggestions

```bash
POST /api/v1/chat/suggest-links
Content-Type: application/json

{
  "todo_id": 42
}
```

## RAG Integration

The chat system will use the existing RAG infrastructure:

1. User query arrives
2. RAG search retrieves relevant chunks
3. Chunks assembled into context
4. LLM generates response with citations
5. Response includes source references

```python
# Planned flow
async def process_message(query: str):
    # Retrieve relevant context
    chunks = await rag.search(query, n_results=5)
    
    # Build prompt with context
    context = format_context(chunks)
    prompt = f"""Answer based on this context:
{context}

Question: {query}"""
    
    # Generate response
    response = await llm.complete(prompt)
    
    return {
        "response": response,
        "sources": [c.knowledge_id for c in chunks]
    }
```

## Implementation Timeline

This feature is planned for a future release. Current priorities:

1. Core todo and knowledge management (complete)
2. RAG indexing and search (complete)
3. Frontend knowledge integration (in progress)
4. Chat interface and LLM integration (planned)

