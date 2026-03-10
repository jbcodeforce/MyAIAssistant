"""Agent service FastAPI app: Agno AgentOS + compatibility routes for backend proxy."""

import logging
import os
import sys
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

from fastapi.middleware.cors import CORSMiddleware
from agno.os import AgentOS

logger.info("Building chat agent (may connect to LLM/Ollama and Knowledge/Chroma)...")
from agent_service.agents.agent_factory import get_or_create_agent_factory
from agent_service.routes import chat_router, health_router, rag_router, extract_router, tag_router, myai_agent_api_router
from agent_service.ai_db import get_ai_db, create_knowledge

config_path = str(Path(__file__).parent.joinpath("config.yaml"))

agent_factory = get_or_create_agent_factory()
agents = agent_factory.list_agents()


try:
    kb = create_knowledge("agent_os", "knowledge_base")
    logger.info("Knowledge (RAG) loaded")
except Exception as e:
    kb = None
    logger.warning("Knowledge not available (RAG disabled): %s", e)


print(f"config_path: {config_path}")
agent_os = AgentOS(
    id="myai-agent-service",
    name="MyAIAssistant Agent Service",
    agents=agents,
    #knowledge=[kb] if kb else [],
    config=config_path,
    tracing=True,
    telemetry=False,
    db=get_ai_db()
)

app = agent_os.get_app()

# CORS so the frontend (e.g. http://localhost:3000) can call this service directly when agent_service_url is set
_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").strip().split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Mounting compatibility routes...")

# My own routes
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(extract_router)
app.include_router(tag_router)
app.include_router(myai_agent_api_router)


logger.info("Agent service app ready")

@app.get("/")
async def root():
    return {"service": "myai-agent-service", "message": "MyAIAssistant Agent Service; use /health, /chat/todo, /chat/generic"}

if __name__ == "__main__":
    agent_os.serve(app="main:app", port=8100, reload=True)
