import pytest
import tempfile
import shutil
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.database import get_db
from app.db.models import Base
from app.api.rag import get_rag
from agent_core.services.rag.service import RAGService
from agent_core.services.rag.service import get_rag_service

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

test_async_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# Test RAG service with temporary directory
_test_rag_service = None
_test_chroma_dir = None


def get_test_rag_service() -> RAGService:
    """Get a test-specific RAG service with isolated storage."""
    global _test_rag_service, _test_chroma_dir
    if _test_rag_service is None:
        _test_chroma_dir = tempfile.mkdtemp(prefix="test_chroma_")
        _test_rag_service = RAGService(
            persist_directory=_test_chroma_dir,
            collection_name="test_knowledge_base"
        )
    return _test_rag_service


def cleanup_test_rag():
    """Clean up the test RAG service."""
    global _test_rag_service, _test_chroma_dir
    if _test_rag_service is not None:
        # Delete all documents from the collection
        try:
            all_ids = _test_rag_service.collection.get()["ids"]
            if all_ids:
                _test_rag_service.collection.delete(ids=all_ids)
        except Exception:
            pass
    if _test_chroma_dir is not None:
        try:
            shutil.rmtree(_test_chroma_dir, ignore_errors=True)
        except Exception:
            pass
        _test_chroma_dir = None
    _test_rag_service = None


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with test_async_session_maker() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override both database and RAG service
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_rag] = get_test_rag_service
    
    # Clean up any previous test data from RAG
    cleanup_test_rag()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Clean up after test
    cleanup_test_rag()
    app.dependency_overrides.clear()

