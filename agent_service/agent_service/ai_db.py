from agno.db.sqlite.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge
import os
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agent_service.agents.agent_config import get_llm_base_url

db_url = os.getenv("AI_DB_URL", "sqlite+aiosqlite:///./data/ai.db")
vs_url = os.getenv("VS_DB_URL", "data/vs.db")


def get_ai_db(contents_table: str | None = None) -> SqliteDb:
    if contents_table is None:
        contents_table = "ai_contents"
    db_file = os.getenv("AI_DB_FILE", "data/ai.db")
    return SqliteDb(db_file=db_file, knowledge_table=contents_table)

def create_knowledge(name: str, table_name: str) -> Knowledge:
    return Knowledge(
        name=name,
        vector_db=LanceDb(
            table_name=table_name,
            uri=vs_url,

        ),
        contents_db=get_ai_db(contents_table=f"{table_name}_cts"),
        max_results=5,
    )

def get_embedder():
    """Ollama embedder; set OLLAMA_BASE_URL and embedder model id if needed."""
    base_url = get_llm_base_url()
    model = os.getenv("KNOWLEDGE_EMBEDDER_MODEL", "nomic-embed-text")
    return OllamaEmbedder(id=model)


