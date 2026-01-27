"""Unit tests for RAGService orchestrator.

Tests for the RAGService class that orchestrates document processing,
vector storage, and retrieval operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from agent_core.services.rag.service import RAGService, SearchResult, IndexingResult
from agent_core.services.rag.vector_store import VectorStore, SearchResults
from agent_core.services.rag.document_processor import DocumentProcessor, KnowledgeItem, KnowledgeChunk
from agent_core.services.rag.document_loader import DocumentLoader, LoadedDocument


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB storage."""
    tmpdir = tempfile.mkdtemp(prefix="rag_service_test_")
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def rag_service(temp_chroma_dir: str) -> RAGService:
    """Create a RAGService instance for testing."""
    return RAGService(
        persist_directory=temp_chroma_dir,
        collection_name="test_knowledge_base",
        chunk_size=500,
        chunk_overlap=100,
        embedding_model="all-MiniLM-L6-v2"
    )


@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample markdown file for testing."""
    content = """# Test Document

This is a test document with content that will be indexed.

## Section 1

First section content for testing.

## Section 2

Second section with more content.
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(content)
    return str(file_path)


class TestRAGServiceInitialization:
    """Tests for RAGService initialization."""

    def test_init_creates_components(self, rag_service: RAGService):
        """Test that initialization creates all components."""
        assert rag_service.vector_store is not None
        assert isinstance(rag_service.vector_store, VectorStore)
        assert rag_service.document_processor is not None
        assert isinstance(rag_service.document_processor, DocumentProcessor)
        assert rag_service.document_loader is not None
        assert isinstance(rag_service.document_loader, DocumentLoader)

    def test_init_with_custom_config(self, temp_chroma_dir: str):
        """Test initialization with custom configuration."""
        service = RAGService(
            persist_directory=temp_chroma_dir,
            collection_name="custom_collection",
            chunk_size=1000,
            chunk_overlap=200,
            embedding_model="all-MiniLM-L6-v2"
        )
        
        assert service.vector_store.max_results == 5  # Default
        assert service.document_processor.chunk_size == 1000
        assert service.document_processor.chunk_overlap == 200


class TestRAGServiceIndexing:
    """Tests for knowledge indexing functionality."""

    @pytest.mark.asyncio
    async def test_index_knowledge_markdown(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test indexing a markdown document."""
        result = await rag_service.index_knowledge(
            knowledge_id=1,
            title="Test Document",
            uri=sample_markdown_file,
            document_type="markdown",
            category="test",
            tags="tag1,tag2"
        )
        
        assert isinstance(result, IndexingResult)
        assert result.success is True
        assert result.chunks_indexed > 0
        assert result.content_hash is not None
        assert result.error is None

    @pytest.mark.asyncio
    async def test_index_knowledge_removes_existing(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test that indexing removes existing chunks first."""
        # Index first time
        result1 = await rag_service.index_knowledge(
            knowledge_id=1,
            title="First Index",
            uri=sample_markdown_file,
            document_type="markdown",
            category="test",
            tags=""
        )
        chunks1 = result1.chunks_indexed
        
        # Index again (should replace)
        result2 = await rag_service.index_knowledge(
            knowledge_id=1,
            title="Second Index",
            uri=sample_markdown_file,
            document_type="markdown",
            category="test",
            tags=""
        )
        chunks2 = result2.chunks_indexed
        
        # Should have same number of chunks (not doubled)
        assert chunks2 == chunks1
        
        # Verify total chunks in store
        stats = rag_service.vector_store.get_collection_stats()
        assert stats["total_chunks"] == chunks1

    @pytest.mark.asyncio
    async def test_index_knowledge_with_optional_fields(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test indexing with optional category and tags."""
        result = await rag_service.index_knowledge(
            knowledge_id=2,
            title="Optional Fields Test",
            uri=sample_markdown_file,
            document_type="markdown",
            category=None,
            tags=None
        )
        
        assert result.success is True
        
        # Verify metadata was stored
        metadata = rag_service.vector_store.get_knowledge_metadata(2)
        assert metadata is not None
        assert metadata["category"] == ""
        assert metadata["tags"] == ""

    @pytest.mark.asyncio
    async def test_index_knowledge_file_not_found(self, rag_service: RAGService):
        """Test indexing with non-existent file."""
        result = await rag_service.index_knowledge(
            knowledge_id=3,
            title="Non-existent",
            uri="file:///nonexistent.md",
            document_type="markdown",
            category="test",
            tags=""
        )
        
        assert result.success is False
        assert result.chunks_indexed == 0
        assert result.error is not None
        assert "not found" in result.error.lower() or "FileNotFoundError" in result.error

    @pytest.mark.asyncio
    async def test_index_knowledge_empty_content(self, rag_service: RAGService, tmp_path):
        """Test indexing empty file."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("")
        
        result = await rag_service.index_knowledge(
            knowledge_id=4,
            title="Empty File",
            uri=str(empty_file),
            document_type="markdown",
            category="test",
            tags=""
        )
        
        # Should handle empty content gracefully
        # May return success with 0 chunks or failure
        assert isinstance(result, IndexingResult)
        assert result.chunks_indexed == 0 or result.success is False


class TestRAGServiceSearch:
    """Tests for search functionality."""

    @pytest.mark.asyncio
    async def test_search_basic(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test basic search functionality."""
        # First index
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Test Document",
            uri=sample_markdown_file,
            document_type="markdown",
            category="test",
            tags=""
        )
        
        # Then search
        results = await rag_service.search(
            query="test document",
            n_results=5
        )
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        
        # Check result structure
        result = results[0]
        assert result.content is not None
        assert result.knowledge_id == 1
        assert result.title is not None
        assert result.score > 0

    @pytest.mark.asyncio
    async def test_search_with_category_filter(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test search with category filter."""
        # Index with category
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Category Test",
            uri=sample_markdown_file,
            document_type="markdown",
            category="programming",
            tags=""
        )
        
        # Search with matching category
        results = await rag_service.search(
            query="test",
            n_results=5,
            category="programming"
        )
        
        assert len(results) > 0
        # All results should be from the category
        # (This depends on implementation - may need adjustment)
        
        # Search with non-matching category
        results_empty = await rag_service.search(
            query="test",
            n_results=5,
            category="nonexistent"
        )
        
        assert len(results_empty) == 0

    @pytest.mark.asyncio
    async def test_search_with_knowledge_ids_filter(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test search filtered by knowledge IDs."""
        # Index multiple items
        for kid in [1, 2]:
            await rag_service.index_knowledge(
                knowledge_id=kid,
                title=f"Doc {kid}",
                uri=sample_markdown_file,
                document_type="markdown",
                category="test",
                tags=""
            )
        
        # Search with filter
        results = await rag_service.search(
            query="test",
            n_results=5,
            knowledge_ids=[1]
        )
        
        # All results should be from knowledge_id 1
        assert all(r.knowledge_id == 1 for r in results)

    @pytest.mark.asyncio
    async def test_search_empty_collection(self, rag_service: RAGService):
        """Test search on empty collection."""
        results = await rag_service.search(
            query="anything",
            n_results=5
        )
        
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_result_scores(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test that search results have scores."""
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Score Test",
            uri=sample_markdown_file,
            document_type="markdown",
            category="test",
            tags=""
        )
        
        results = await rag_service.search(
            query="test document",
            n_results=5
        )
        
        assert len(results) > 0
        # Scores should be between 0 and 1 (for cosine similarity)
        for result in results:
            assert 0 <= result.score <= 1

    @pytest.mark.asyncio
    async def test_search_result_metadata(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test that search results include proper metadata."""
        await rag_service.index_knowledge(
            knowledge_id=5,
            title="Metadata Test",
            uri=sample_markdown_file,
            document_type="markdown",
            category="test",
            tags="tag1"
        )
        
        results = await rag_service.search(
            query="test",
            n_results=1
        )
        
        assert len(results) > 0
        result = results[0]
        assert result.knowledge_id == 5
        assert result.title == "Metadata Test"
        assert result.uri == sample_markdown_file
        assert result.chunk_index >= 0


class TestRAGServiceRemoval:
    """Tests for removing knowledge items."""

    @pytest.mark.asyncio
    async def test_remove_knowledge(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test removing a knowledge item."""
        # Index first
        result = await rag_service.index_knowledge(
            knowledge_id=1,
            title="To Remove",
            uri=sample_markdown_file,
            document_type="markdown",
            category="test",
            tags=""
        )
        assert result.success is True
        
        # Remove
        success = await rag_service.remove_knowledge(1)
        
        assert success is True
        
        # Verify removal
        stats = rag_service.vector_store.get_collection_stats()
        assert stats["total_chunks"] == 0
        assert stats["unique_knowledge_items"] == 0
        
        # Metadata should also be removed
        metadata = rag_service.vector_store.get_knowledge_metadata(1)
        assert metadata is None

    @pytest.mark.asyncio
    async def test_remove_knowledge_not_found(self, rag_service: RAGService):
        """Test removing non-existent knowledge item."""
        success = await rag_service.remove_knowledge(999)
        
        # Should succeed even if nothing to remove
        assert success is True


class TestRAGServiceStats:
    """Tests for collection statistics."""

    @pytest.mark.asyncio
    async def test_get_collection_stats(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test getting collection statistics."""
        # Index some items
        for kid in [1, 2]:
            await rag_service.index_knowledge(
                knowledge_id=kid,
                title=f"Doc {kid}",
                uri=sample_markdown_file,
                document_type="markdown",
                category="test",
                tags=""
            )
        
        stats = rag_service.get_collection_stats()
        
        assert stats["total_chunks"] > 0
        assert stats["unique_knowledge_items"] == 2
        assert "collection_name" in stats
        assert "embedding_model" in stats

    @pytest.mark.asyncio
    async def test_get_collection_stats_empty(self, rag_service: RAGService):
        """Test stats for empty collection."""
        stats = rag_service.get_collection_stats()
        
        assert stats["total_chunks"] == 0
        assert stats["unique_knowledge_items"] == 0


class TestRAGServiceIntegration:
    """Integration tests for full RAG workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        rag_service: RAGService,
        sample_markdown_file: str
    ):
        """Test complete workflow: index, search, remove."""
        # 1. Index
        index_result = await rag_service.index_knowledge(
            knowledge_id=1,
            title="Workflow Test",
            uri=sample_markdown_file,
            document_type="markdown",
            category="test",
            tags="workflow"
        )
        assert index_result.success is True
        assert index_result.chunks_indexed > 0
        
        # 2. Search
        search_results = await rag_service.search(
            query="test document",
            n_results=3
        )
        assert len(search_results) > 0
        
        # 3. Verify stats
        stats = rag_service.get_collection_stats()
        assert stats["total_chunks"] == index_result.chunks_indexed
        assert stats["unique_knowledge_items"] == 1
        
        # 4. Remove
        remove_success = await rag_service.remove_knowledge(1)
        assert remove_success is True
        
        # 5. Verify removal
        final_stats = rag_service.get_collection_stats()
        assert final_stats["total_chunks"] == 0
        assert final_stats["unique_knowledge_items"] == 0

    @pytest.mark.asyncio
    async def test_multiple_knowledge_items(
        self,
        rag_service: RAGService,
        tmp_path
    ):
        """Test working with multiple knowledge items."""
        # Create multiple test files
        files = []
        for i in range(3):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(f"# Document {i}\n\nContent for document {i}.")
            files.append(str(file_path))
        
        # Index all
        for i, file_path in enumerate(files):
            result = await rag_service.index_knowledge(
                knowledge_id=i + 1,
                title=f"Document {i}",
                uri=file_path,
                document_type="markdown",
                category="test",
                tags=f"doc{i}"
            )
            assert result.success is True
        
        # Verify all indexed
        stats = rag_service.get_collection_stats()
        assert stats["unique_knowledge_items"] == 3
        
        # Search should find content from all
        results = await rag_service.search(
            query="document",
            n_results=10
        )
        assert len(results) > 0
        
        # Results should come from different knowledge items
        knowledge_ids = set(r.knowledge_id for r in results)
        assert len(knowledge_ids) >= 1  # At least one should be found
