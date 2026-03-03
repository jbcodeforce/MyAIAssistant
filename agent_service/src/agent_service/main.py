"""Agent service FastAPI app: Agno AgentOS + compatibility routes for backend proxy."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Configure logging first so we see output during import/startup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("agent_service")

logger.info("Loading agent_service.main...")

from fastapi import FastAPI
from agno.os import AgentOS

logger.info("Building chat agent (may connect to LLM/Ollama and Knowledge/Chroma)...")
from agent_service.agents.chat import get_chat_agent
from agent_service.knowledge import get_knowledge
from agent_service.routes import chat_router, health_router, rag_router, extract_router, tag_router

config_path = str(Path(__file__).joinpath("config.yaml"))

chat_agent = get_chat_agent()
logger.info("Chat agent ready")

try:
    kb = get_knowledge()
    logger.info("Knowledge (RAG) loaded")
except Exception as e:
    kb = None
    logger.warning("Knowledge not available (RAG disabled): %s", e)


agent_os = AgentOS(
    id="myai-agent-service",
    name="MyAIAssistant Agent Service",
    agents=[chat_agent],
    knowledge=[kb] if kb else [],
    config=config_path,
    tracing=True

)

app = agent_os.get_app()
logger.info("Mounting compatibility routes...")

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(extract_router)
app.include_router(tag_router)

# Replace deprecated on_event("startup") with lifespan: wrap router's lifespan so our log runs at startup
_original_lifespan = getattr(app.router, "lifespan_context", None)

@asynccontextmanager
async def _agent_service_lifespan():
    if _original_lifespan is not None:
        async with _original_lifespan:
            logger.info("Uvicorn startup complete; agent_service listening for requests")
            yield
    else:
        logger.info("Uvicorn startup complete; agent_service listening for requests")
        yield

app.router.lifespan_context = _agent_service_lifespan()

logger.info("Agent service app ready")


@app.get("/")
async def root():
    return {"service": "agent-service", "message": "MyAIAssistant Agent Service; use /health, /chat/todo, /chat/generic"}
