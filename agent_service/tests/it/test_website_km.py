from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.db.sqlite.sqlite import SqliteDb
from agno.models.ollama import Ollama

contents_db = SqliteDb(
    db_file="data/contents.db",
    knowledge_table="flink-km",
)

vector_db = LanceDb(
    table_name="test_collection",
    uri="data/vs.db",
)



def create_sync_knowledge() -> Knowledge:
    return Knowledge(
        name="My AI Assistant Knowledge Base",
        description="Flink Knowledge Implementation",
        vector_db=vector_db,
        contents_db=contents_db,
    )

if __name__ == "__main__":
    url = "https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/table/tuning/"
    knowledge = create_sync_knowledge()
    knowledge.insert(name= "flink-performance-tuning",
        url=url,
        metadata= {"user_tags": "flink_performance"},
         skip_if_exists=True)
    agent = Agent(
        name="My AI Assistant",
        description="My AI Assistant",
        model=Ollama(id="mistral:7b-instruct"),
        knowledge=knowledge,
        search_knowledge=True,
        debug_mode=True,
    )
    agent.print_response(
        "What is flink minibatch aggregation?",
        markdown=True,
    )
    knowledge.remove_vectors_by_name("flink-performance-tuning")