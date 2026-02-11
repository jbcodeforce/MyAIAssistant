import pytest
import pytest_asyncio
import tempfile
import shutil
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db
from app.db.models import Base
from app.api.rag import get_rag
from agent_core.services.rag.service import RAGService
from agent_core.services.rag.service import get_rag_service

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

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
    """Clean up the test RAG service (clear Chroma content and metadata)."""
    global _test_rag_service, _test_chroma_dir
    if _test_rag_service is not None:
        try:
            vs = _test_rag_service.vector_store
            for coll in (vs.knowledge_content, vs.knowledge_metadata):
                result = coll.get(include=[])
                ids = result.get("ids") or []
                if ids:
                    coll.delete(ids=ids)
        except Exception:
            pass
    if _test_chroma_dir is not None:
        try:
            shutil.rmtree(_test_chroma_dir, ignore_errors=True)
        except Exception:
            pass
        _test_chroma_dir = None
    _test_rag_service = None


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create engine with StaticPool for in-memory SQLite
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Provide session
    async with async_session_maker() as session:
        yield session
    
    # Drop tables and dispose engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database and RAG overrides."""
    # Create engine for the override function
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()
    
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
    
    # Dispose engine
    await engine.dispose()
