# Agent Core

A library for building agentic AI applications with unified LLM integration. Provides both synchronous and asynchronous APIs, agent framework components, and intelligent query routing.

## Features

- Unified LLM client supporting OpenAI, Anthropic, and Ollama
- Both synchronous and asynchronous APIs
- Agent framework with base classes for specialized agents
- Query classification for intent detection
- Agent router for intelligent query routing

## Installation

```bash
# From the MyAIAssistant root directory
uv pip install -e agent_core/
```

## LLM Client Usage

### Async API (for FastAPI/async applications)

```python
from agent_core import LLMClient, LLMConfig, Message

config = LLMConfig(
    provider="openai",
    model="gpt-4",
    api_key="your-api-key"
)

client = LLMClient(config)

messages = [
    Message(role="system", content="You are a helpful assistant."),
    Message(role="user", content="Hello!")
]

response = await client.chat_async(messages)
print(response.content)
```

### Sync API (for CLI/scripts)

```python
from agent_core import LLMClient, LLMConfig, Message

config = LLMConfig(
    provider="ollama",
    model="llama2"
)

client = LLMClient(config)
response = client.chat(messages)
print(response.content)
```

## Agent Framework

### Creating Custom Agents

```python
from agent_core import BaseAgent, AgentResponse, LLMConfig

class MyAgent(BaseAgent):
    agent_type = "my_agent"
    
    async def execute(self, query, conversation_history=None, context=None):
        system_prompt = self.build_system_prompt(context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        response = await self._call_llm(messages)
        return AgentResponse(
            message=response,
            model=self.model,
            provider=self.provider,
            agent_type=self.agent_type
        )
    
    def build_system_prompt(self, context=None):
        return "You are a specialized assistant."

# Create agent with config
config = LLMConfig(provider="openai", model="gpt-4", api_key="...")
agent = MyAgent(llm_config=config)

# Or with individual parameters
agent = MyAgent(provider="openai", model="gpt-4", api_key="...")
```

### Query Classification

```python
from agent_core import QueryClassifier, LLMConfig

config = LLMConfig(provider="openai", model="gpt-4", api_key="...")
classifier = QueryClassifier(llm_config=config)

result = await classifier.classify("How do I implement OAuth?")
print(result.intent)      # QueryIntent.CODE_HELP
print(result.confidence)  # 0.95
print(result.entities)    # {"topic": "OAuth", "keywords": ["auth"]}
```

### Agent Routing

```python
from agent_core import AgentRouter, QueryClassifier, QueryIntent

# Create your specialized agents
rag_agent = MyRAGAgent(llm_config=config)
code_agent = MyCodeAgent(llm_config=config)
general_agent = MyGeneralAgent(llm_config=config)

# Create router
router = AgentRouter(
    classifier=QueryClassifier(llm_config=config),
    agents={
        "rag": rag_agent,
        "code": code_agent,
        "general": general_agent,
    },
    intent_mapping={
        QueryIntent.KNOWLEDGE_SEARCH: "rag",
        QueryIntent.CODE_HELP: "code",
        QueryIntent.GENERAL_CHAT: "general",
    }
)

# Route queries
response = await router.route("How do I implement OAuth?")
print(response.message)      # Response from code_agent
print(response.intent)       # QueryIntent.CODE_HELP
print(response.agent_type)   # "code"
```

## Configuration

```python
from agent_core import LLMConfig

config = LLMConfig(
    provider="openai",      # "openai", "anthropic", "ollama"
    model="gpt-4",          # Model name
    api_key="...",          # API key (not needed for Ollama)
    base_url=None,          # Custom base URL (optional)
    max_tokens=2048,        # Max response tokens
    temperature=0.7,        # Sampling temperature
    timeout=60.0,           # Request timeout in seconds
)
```

## Supported Intents

The query classifier recognizes these intent types:

- `KNOWLEDGE_SEARCH` - Information retrieval from knowledge base
- `TASK_PLANNING` - Task breakdown and planning
- `TASK_STATUS` - Status of existing tasks
- `CODE_HELP` - Programming assistance
- `GENERAL_CHAT` - General conversation
- `UNCLEAR` - Ambiguous queries needing clarification

## Run all integration tests
```sh
uv run pytest tests/it/ -v -m integration

# Run specific classification test
uv run pytest tests/it/test_agent_router_ollama.py::TestQueryClassifierOllama::test_classify_knowledge_search_query -v

# Override the model
OLLAMA_TEST_MODEL=qwen3-coder:30b uv run pytest tests/it/ -v -m integration
```