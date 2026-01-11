# Agent Core

A library for building agentic AI applications with unified LLM integration via HuggingFace InferenceClient. Provides both synchronous and asynchronous APIs, a config-driven agent framework, and intelligent query routing.

## Features

- Unified LLM client using HuggingFace InferenceClient
- Supports both local inference servers (TGI, vLLM, Ollama) and HuggingFace Hub remote models
- Both synchronous and asynchronous APIs
- Config-driven agent framework with YAML-based agent definitions
- Agent factory for creating agents from configuration
- Query classification for intent detection
- Agent router for intelligent query routing

## Installation

```bash
# From the MyAIAssistant root directory
uv pip install -e agent_core/
```

## Architecture

The agent framework uses a config-driven design where agents are defined by YAML configuration files and markdown prompt templates.

```
agent_core/
├── agents/
│   ├── config/                    # Agent configurations
│   │   ├── QueryClassifier/
│   │   │   ├── agent.yaml         # Agent configuration
│   │   │   └── prompt.md          # System prompt template
│   │   ├── GeneralAgent/
│   │   ├── RAGAgent/
│   │   ├── CodeAgent/
│   │   └── TaskAgent/
│   ├── base_agent.py              # BaseAgent, AgentInput, AgentOutput
│   ├── factory.py                 # AgentFactory, AgentConfig
│   ├── query_classifier.py        # QueryClassifier agent
│   ├── agent_router.py            # AgentRouter for query routing
│   └── ...
├── client.py                      # LLMClient
├── config.py                      # Configuration utilities
└── types.py                       # Message, LLMResponse
```

## Agent Factory

The `AgentFactory` discovers and creates agents from YAML configuration files. Each agent is defined by a directory in `agents/config/` containing an `agent.yaml` and  `prompt.md`.

### Using the Factory

```python
from agent_core.agents import AgentFactory

# Create factory (auto-discovers agents from config/)
factory = AgentFactory()

# List available agents
print(factory.list_agents())
# ['QueryClassifier', 'GeneralAgent', 'RAGAgent', 'CodeAgent', 'TaskAgent']

# Create an agent by name, the name matches the directory name
agent = factory.create_agent("GeneralAgent")

# Execute the agent
response = await agent.execute("Hello, how are you?")
print(response.message)
```

### Agent Configuration Schema

`AgentConfig` is the unified configuration class that combines agent-specific settings with LLM configuration. Each agent is defined by an `agent.yaml` file:

```yaml
name: GeneralAgent
description: General purpose assistant for conversation
class: agent_core.agents.general_agent.GeneralAgent  # Fully qualified class name
provider: huggingface        # LLM provider
model: gpt-4o-mini           # Model identifier
api_key: null                # API key (optional, uses HF_TOKEN env var)
base_url: null               # Base URL for local servers (optional)
temperature: 0.7             # Sampling temperature
max_tokens: 2048             # Max response tokens
timeout: 60.0                # Request timeout in seconds
```

Configuration fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent name (matches directory name) |
| `description` | string | Human-readable description |
| `class` | string | Fully qualified Python class name (e.g., `module.path.ClassName`) |
| `provider` | string | LLM provider (default: huggingface) |
| `model` | string | Model identifier |
| `api_key` | string | API key for remote models (optional) |
| `base_url` | string | Base URL for local inference servers (optional) |
| `temperature` | float | Sampling temperature (default: 0.7) |
| `max_tokens` | int | Maximum response tokens (default: 2048) |
| `timeout` | float | Request timeout in seconds (default: 60.0) |

The `class` field uses fully qualified class names to enable dynamic import. If omitted, `GeneralAgent` is used as the default.

### Using AgentConfig Programmatically

```python
from agent_core import AgentConfig, LLMClient

# Create configuration
config = AgentConfig(
    name="MyAgent",
    provider="huggingface",
    model="gpt-4o-mini",
    base_url="http://localhost:8080",
    temperature=0.5
)

# Validate configuration
config.validate()

# Use directly with LLMClient
client = LLMClient(config)
```

### System Prompts

Each agent can have a `prompt.md` file containing the system prompt template:

```markdown
You are a helpful AI assistant.
Be clear and concise in your responses.

## Instructions
- Be helpful and friendly
- Provide accurate information
```

Prompts support template variables using `{variable}` syntax:

```markdown
You are a code assistant.

## Technical Context
Language: {language}
Framework: {framework}

## User Query
{query}
```

### Creating Custom Agents

Define a new agent by creating a config directory:

```
agents/config/MyCustomAgent/
├── agent.yaml
└── prompt.md
```

Create the `agent.yaml` with your fully qualified class name:

```yaml
name: MyCustomAgent
description: My custom agent
class: my_package.agents.MyCustomAgent
provider: huggingface
model: gpt-4o-mini
temperature: 0.7
max_tokens: 2048
```

Create a Python class extending `BaseAgent`:

```python
# my_package/agents.py
from agent_core.agents import BaseAgent, AgentResponse

class MyCustomAgent(BaseAgent):
    agent_type = "my_custom"
    
    async def execute(self, query, conversation_history=None, context=None):
        # Custom execution logic
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
```

The factory will dynamically import your class using the fully qualified name.

Alternatively, register a class manually for short name access:

```python
from agent_core.agents import AgentFactory
from my_package.agents import MyCustomAgent

AgentFactory.register_class("my_package.agents.MyCustomAgent", MyCustomAgent)
```

## Base Types

### AgentInput

Standard input structure for agent execution:

```python
from agent_core.agents import AgentInput

input_data = AgentInput(
    query="What is OAuth?",
    conversation_history=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ],
    context={"task_id": "123"}
)
```

### AgentOutput

Standard output structure from agent execution:

```python
from agent_core.agents import AgentOutput

output = AgentOutput(
    message="OAuth is an authorization protocol...",
    metadata={"intent": "code_help", "confidence": 0.95}
)
```

### AgentResponse

Extended output with full execution context:

```python
from agent_core.agents import AgentResponse

response = AgentResponse(
    message="Response text",
    context_used=[{"title": "doc.md", "uri": "path/to/doc"}],
    model="gpt-4o-mini",
    provider="huggingface",
    agent_type="rag",
    metadata={"search_query": "oauth"}
)
```

## LLM Client Usage

### Local Inference Server (TGI, vLLM, Ollama)

```python
from agent_core import LLMClient, AgentConfig, Message

config = AgentConfig(
    name="LocalLLM",
    provider="huggingface",
    model="llama3",
    base_url="http://localhost:8080"
)

client = LLMClient(config)

messages = [
    Message(role="system", content="You are a helpful assistant."),
    Message(role="user", content="Hello!")
]

# Async usage
response = await client.chat_async(messages)
print(response.content)

# Sync usage
response = client.chat(messages)
print(response.content)
```

### HuggingFace Hub (Remote Models)

```python
import os
from agent_core import LLMClient, AgentConfig, Message

config = AgentConfig(
    name="HFHub",
    provider="huggingface",
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    api_key=os.getenv("HF_TOKEN")
)

client = LLMClient(config)
response = await client.chat_async([
    Message(role="user", content="Hello!")
])
print(response.content)
```

## Query Classification

The `QueryClassifier` analyzes user queries to determine intent for routing:

```python
from agent_core.agents import QueryClassifier

classifier = QueryClassifier(
    provider="huggingface",
    model="gpt-4o-mini"
)

result = await classifier.classify("How do I implement OAuth?")
print(result.intent)      # QueryIntent.CODE_HELP
print(result.confidence)  # 0.95
print(result.entities)    # {"topic": "OAuth", "keywords": ["auth"]}
```

Or create via factory:

```python
from agent_core.agents import AgentFactory

factory = AgentFactory()
classifier = factory.create_agent("QueryClassifier")

# Use the execute() method for standard agent interface
response = await classifier.execute("How do I implement OAuth?")
print(response.metadata["intent"])  # "code_help"

# Or use classify() for ClassificationResult
result = await classifier.classify("How do I implement OAuth?")
```

### Supported Intents

| Intent | Description |
|--------|-------------|
| `KNOWLEDGE_SEARCH` | Information retrieval from knowledge base |
| `TASK_PLANNING` | Task breakdown and planning |
| `TASK_STATUS` | Status of existing tasks |
| `CODE_HELP` | Programming assistance |
| `GENERAL_CHAT` | General conversation |
| `RESEARCH` | Research queries |
| `UNCLEAR` | Ambiguous queries needing clarification |

## Agent Routing

The `AgentRouter` classifies queries and routes them to specialized agents:

```python
from agent_core.agents import AgentRouter, QueryIntent, get_agent_router

# Use the default router (auto-configured with all agents)
router = get_agent_router()

# Route a query
response = await router.route("How do I implement OAuth?")
print(response.message)      # Response from code_agent
print(response.intent)       # QueryIntent.CODE_HELP
print(response.agent_type)   # "code_help"

# Force a specific intent
response = await router.route(
    "What is OAuth?",
    force_intent=QueryIntent.KNOWLEDGE_SEARCH
)
```

### Custom Router Configuration

```python
from agent_core.agents import AgentRouter, QueryClassifier, QueryIntent

# Create custom agents
rag_agent = factory.create_agent("RAGAgent")
code_agent = factory.create_agent("CodeAgent")
general_agent = factory.create_agent("GeneralAgent")

# Create router with custom configuration
router = AgentRouter(
    classifier=factory.create_agent("QueryClassifier"),
    agents={
        "rag": rag_agent,
        "code": code_agent,
        "general": general_agent,
    },
    intent_mapping={
        QueryIntent.KNOWLEDGE_SEARCH: "rag",
        QueryIntent.CODE_HELP: "code",
        QueryIntent.GENERAL_CHAT: "general",
    },
    default_agent="general"
)
```

## Configuration

### AgentConfig

`AgentConfig` is the unified configuration class that includes both agent-specific settings and LLM configuration. Use it for agents and LLMClient:

```python
from agent_core import AgentConfig, LLMClient

config = AgentConfig(
    name="MyAgent",
    description="My custom agent",
    agent_class="my_module.MyAgent",  # Fully qualified class name
    provider="huggingface",
    model="gpt-4o-mini",
    base_url="http://localhost:8080",
    temperature=0.7,
    max_tokens=2048,
    timeout=60.0,
)

# Use with LLMClient
client = LLMClient(config)

# Validate configuration
config.validate()
```

Configuration fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent name (matches directory name) |
| `description` | string | Human-readable description |
| `agent_class` | string | Fully qualified Python class name |
| `provider` | string | LLM provider (default: huggingface) |
| `model` | string | Model name (HF model ID or local model name) |
| `api_key` | string | HF_TOKEN for remote models (not needed for local) |
| `base_url` | string | Base URL for local inference servers |
| `max_tokens` | int | Max response tokens (default: 2048) |
| `temperature` | float | Sampling temperature (default: 0.7) |
| `timeout` | float | Request timeout in seconds (default: 60.0) |

### Environment Variables

Create a `.env` file in your project root:

```bash
HF_TOKEN=hf_your_token_here
```

The library automatically loads environment variables using `python-dotenv`.

## Built-in Agents

| Agent | Description | Use Case |
|-------|-------------|----------|
| `QueryClassifier` | Classifies user queries for routing | Intent detection |
| `GeneralAgent` | General-purpose assistant | Conversation, Q&A |
| `RAGAgent` | Knowledge base search with RAG | Document retrieval |
| `CodeAgent` | Programming assistance | Code help, debugging |
| `TaskAgent` | Task planning and management | Task breakdown |

## Testing

```bash
# Run unit tests
uv run pytest tests/ut/ -v

# Run integration tests
uv run pytest tests/it/ -v -m integration

# Run specific test file
uv run pytest tests/ut/test_agent_factory.py -v
```

## API Reference

### Factory Functions

```python
from agent_core.agents import (
    AgentFactory,           # Factory class
    AgentConfig,            # Configuration dataclass
    get_agent_factory,      # Get singleton factory
    reset_agent_factory,    # Reset singleton (for testing)
)
```

### Agent Base Classes

```python
from agent_core.agents import (
    BaseAgent,              # Abstract base class
    AgentInput,             # Standard input structure
    AgentOutput,            # Standard output structure
    AgentResponse,          # Extended response with context
)
```

### Query Classification

```python
from agent_core.agents import (
    QueryClassifier,        # Classifier agent
    QueryIntent,            # Intent enum
    ClassificationResult,   # Classification output
    CLASSIFICATION_PROMPT,  # Default prompt template
)
```

### Routing

```python
from agent_core.agents import (
    AgentRouter,            # Router class
    WorkflowState,          # Internal state
    RoutedResponse,         # Router response
    get_agent_router,       # Get singleton router
    reset_agent_router,     # Reset singleton
)
```
