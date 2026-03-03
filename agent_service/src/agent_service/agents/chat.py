"""Main chat agent with Knowledge/RAG for backend compatibility."""

import logging
import os
from pathlib import Path

from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.db.sqlite import SqliteDb

from agent_service.config import get_llm_base_url, get_llm_model
from agent_service.knowledge import get_knowledge

logger = logging.getLogger("agent_service.agents.chat")


INSTRUCTIONS = """\
You are a helpful assistant for task planning and general questions.
Use the provided knowledge base context when relevant to answer the user.
Be concise and actionable. For task-related queries, suggest clear next steps.
"""


def _build_model():
    base_url = get_llm_base_url()
    model = get_llm_model()
    return OpenAILike(
        id=model,
        base_url=base_url,
        temperature=0.2,
        api_key=os.getenv("LLM_API_KEY", "no-key"),
    )


_db: SqliteDb | None = None
_agent: Agent | None = None


def get_chat_agent() -> Agent:
    """Return the singleton chat agent (with knowledge/RAG when available)."""
    global _agent, _db
    if _agent is None:
        logger.info("Initializing chat agent...")
        db_path = os.getenv("AGENT_DB_PATH", "data/agents.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _db = SqliteDb(db_file=db_path)
        logger.info("Loading knowledge for RAG (may connect to Ollama/Chroma)...")
        try:
            kb = get_knowledge()
            logger.info("Knowledge attached to chat agent")
        except Exception as e:
            logger.warning("Knowledge unavailable: %s", e)
            kb = None
        base_url = get_llm_base_url()
        model = get_llm_model()
        logger.info("Building LLM client: base_url=%s model=%s", base_url, model)
        _agent = Agent(
            name="Chat Agent",
            model=_build_model(),
            instructions=INSTRUCTIONS,
            db=_db,
            knowledge=kb,
            search_knowledge=kb is not None,
            add_datetime_to_context=True,
            add_history_to_context=True,
            num_history_runs=10,
            markdown=True,
        )
    return _agent


# For AgentOS: pass get_chat_agent() when building the OS so agent is created after config
