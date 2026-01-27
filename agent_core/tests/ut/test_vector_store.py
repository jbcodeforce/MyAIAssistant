"""Unit tests for VectorStore component.

Tests for the VectorStore class that manages ChromaDB collections
for knowledge metadata and content chunks.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

from agent_core.services.rag.vector_store import VectorStore, SearchResults
from agent_core.services.rag.text_splitter import TextChunk


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB storage."""
    tmpdir = tempfile.mkdtemp(prefix="vector_store_test_")
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def vector_store(temp_chroma_dir: str) -> VectorStore:
    """Create a VectorStore instance for testing."""
    return VectorStore(
        chroma_path=temp_chroma_dir,
        embedding_model="all-MiniLM-L6-v2",
        max_results=5
    )


class TestVectorStoreInitialization:
    """Tests for VectorStore initialization."""

    def test_init_creates_collections(self, vector_store: VectorStore):
        """Test that initialization creates both collections."""
        assert vector_store.knowledge_metadata is not None
        assert vector_store.knowledge_content is not None
        assert vector_store.max_results == 5

    def test_init_with_custom_max_results(self, temp_chroma_dir: str):
        """Test initialization with custom max_results."""
        store = VectorStore(
            chroma_path=temp_chroma_dir,
            embedding_model="all-MiniLM-L6-v2",
            max_results=10
        )
        assert store.max_results == 10


class TestVectorStoreMetadata:
    """Tests for knowledge metadata operations."""

    def test_add_knowledge_metadata(self, vector_store: VectorStore):
        """Test adding knowledge metadata to the catalog."""
        vector_store.add_knowledge_metadata(
            knowledge_id=1,
            title="Test Document",
            uri="file:///test.md",
            category="test",
            tags="tag1,tag2"
        )
        
        # Verify metadata was added
        results = vector_store.knowledge_metadata.get(ids=["1"])
        assert len(results["ids"]) == 1
        assert results["metadatas"][0]["title"] == "Test Document"
        assert results["metadatas"][0]["uri"] == "file:///test.md"
        assert results["metadatas"][0]["category"] == "test"
        assert results["metadatas"][0]["tags"] == "tag1,tag2"

    def test_add_knowledge_metadata_with_optional_fields(self, vector_store: VectorStore):
        """Test adding metadata with optional fields as None."""
        vector_store.add_knowledge_metadata(
            knowledge_id=2,
            title="Another Document",
            uri="file:///another.md",
            category=None,
            tags=None
        )
        
        results = vector_store.knowledge_metadata.get(ids=["2"])
        metadata = results["metadatas"][0]
        assert metadata["category"] == ""
        assert metadata["tags"] == ""

    def test_get_knowledge_metadata(self, vector_store: VectorStore):
        """Test retrieving knowledge metadata."""
        vector_store.add_knowledge_metadata(
            knowledge_id=3,
            title="Retrieved Document",
            uri="file:///retrieved.md",
            category="docs",
            tags="important"
        )
        
        metadata = vector_store.get_knowledge_metadata(3)
        assert metadata is not None
        assert metadata["title"] == "Retrieved Document"
        assert metadata["uri"] == "file:///retrieved.md"
        assert metadata["category"] == "docs"
        assert metadata["tags"] == "important"

    def test_get_knowledge_metadata_not_found(self, vector_store: VectorStore):
        """Test retrieving non-existent metadata returns None."""
        metadata = vector_store.get_knowledge_metadata(999)
        assert metadata is None

    def test_get_existing_knowledge_ids(self, vector_store: VectorStore):
        """Test getting list of existing knowledge IDs."""
        # Add multiple knowledge items
        for i in range(1, 4):
            vector_store.add_knowledge_metadata(
                knowledge_id=i,
                title=f"Document {i}",
                uri=f"file:///doc{i}.md",
                category="test",
                tags=""
            )
        
        knowledge_ids = vector_store.get_existing_knowledge_ids()
        assert len(knowledge_ids) == 3
        assert set(knowledge_ids) == {"1", "2", "3"}

    def test_get_knowledge_count(self, vector_store: VectorStore):
        """Test getting count of knowledge items."""
        assert vector_store.get_knowledge_count() == 0
        
        for i in range(1, 6):
            vector_store.add_knowledge_metadata(
                knowledge_id=i,
                title=f"Doc {i}",
                uri=f"file:///doc{i}.md",
                category="test",
                tags=""
            )
        
        assert vector_store.get_knowledge_count() == 5


class TestVectorStoreContent:
    """Tests for knowledge content operations."""

    def test_add_knowledge_content(self, vector_store: VectorStore):
        """Test adding knowledge content chunks."""
        chunks = [
            TextChunk(
                content="First chunk of content",
                start_index=0,
                chunk_index=0,
                metadata={"knowledge_id": 1, "title": "Test Doc"}
            ),
            TextChunk(
                content="Second chunk of content",
                start_index=100,
                chunk_index=1,
                metadata={"knowledge_id": 1, "title": "Test Doc"}
            )
        ]
        
        vector_store.add_knowledge_content(chunks)
        
        # Verify chunks were added
        results = vector_store.knowledge_content.get()
        assert len(results["ids"]) == 2
        assert "First chunk" in results["documents"][0]
        assert "Second chunk" in results["documents"][1]

    def test_add_knowledge_content_empty_list(self, vector_store: VectorStore):
        """Test adding empty chunk list does nothing."""
        vector_store.add_knowledge_content([])
        
        results = vector_store.knowledge_content.get()
        assert len(results["ids"]) == 0

    def test_add_knowledge_content_with_metadata(self, vector_store: VectorStore):
        """Test that chunk metadata is preserved."""
        chunks = [
            TextChunk(
                content="Content with metadata",
                start_index=0,
                chunk_index=0,
                metadata={
                    "knowledge_id": 5,
                    "title": "Metadata Test",
                    "uri": "file:///meta.md",
                    "category": "test",
                    "chunk_index": 0
                }
            )
        ]
        
        vector_store.add_knowledge_content(chunks)
        
        results = vector_store.knowledge_content.get()
        metadata = results["metadatas"][0]
        assert metadata["knowledge_id"] == 5
        assert metadata["title"] == "Metadata Test"
        assert metadata["uri"] == "file:///meta.md"
        assert metadata["category"] == "test"


class TestVectorStoreSearch:
    """Tests for search functionality."""

    def test_search_basic(self, vector_store: VectorStore):
        """Test basic search without filters."""
        # Add metadata and content
        vector_store.add_knowledge_metadata(
            knowledge_id=1,
            title="Python Guide",
            uri="file:///python.md",
            category="programming",
            tags="python"
        )
        
        chunks = [
            TextChunk(
                content="Python is a high-level programming language",
                start_index=0,
                chunk_index=0,
                metadata={"knowledge_id": 1, "title": "Python Guide"}
            ),
            TextChunk(
                content="Python supports object-oriented programming",
                start_index=50,
                chunk_index=1,
                metadata={"knowledge_id": 1, "title": "Python Guide"}
            )
        ]
        vector_store.add_knowledge_content(chunks)
        
        # Search
        results = vector_store.search("What is Python?")
        
        assert isinstance(results, SearchResults)
        assert not results.is_empty()
        assert len(results.documents) > 0
        assert len(results.metadata) > 0
        assert len(results.distances) > 0
        assert results.error is None

    def test_search_with_knowledge_id_filter(self, vector_store: VectorStore):
        """Test search filtered by knowledge_id."""
        # Add two knowledge items
        for kid in [1, 2]:
            vector_store.add_knowledge_metadata(
                knowledge_id=kid,
                title=f"Doc {kid}",
                uri=f"file:///doc{kid}.md",
                category="test",
                tags=""
            )
            chunks = [
                TextChunk(
                    content=f"Content for document {kid}",
                    start_index=0,
                    chunk_index=0,
                    metadata={"knowledge_id": kid, "title": f"Doc {kid}"}
                )
            ]
            vector_store.add_knowledge_content(chunks)
        
        # Search with filter
        results = vector_store.search("document", knowledge_id=1)
        
        assert not results.is_empty()
        # All results should be from knowledge_id 1
        for meta in results.metadata:
            assert meta["knowledge_id"] == 1

    def test_search_with_category_filter(self, vector_store: VectorStore):
        """Test search filtered by category."""
        # Add items with different categories
        for cat in ["programming", "math"]:
            vector_store.add_knowledge_metadata(
                knowledge_id=1 if cat == "programming" else 2,
                title=f"{cat.title()} Guide",
                uri=f"file:///{cat}.md",
                category=cat,
                tags=""
            )
            chunks = [
                TextChunk(
                    content=f"Content about {cat}",
                    start_index=0,
                    chunk_index=0,
                    metadata={
                        "knowledge_id": 1 if cat == "programming" else 2,
                        "title": f"{cat.title()} Guide",
                        "category": cat
                    }
                )
            ]
            vector_store.add_knowledge_content(chunks)
        
        # Search with category filter
        results = vector_store.search("programming", category="programming")
        
        assert not results.is_empty()
        for meta in results.metadata:
            assert meta["category"] == "programming"

    def test_search_with_custom_limit(self, vector_store: VectorStore):
        """Test search with custom result limit."""
        # Add multiple chunks
        chunks = [
            TextChunk(
                content=f"Chunk {i} content",
                start_index=i * 100,
                chunk_index=i,
                metadata={"knowledge_id": 1, "title": "Multi-chunk Doc"}
            )
            for i in range(10)
        ]
        vector_store.add_knowledge_content(chunks)
        
        # Search with limit
        results = vector_store.search("chunk", limit=3)
        
        assert len(results.documents) <= 3

    def test_search_empty_collection(self, vector_store: VectorStore):
        """Test search on empty collection returns empty results."""
        results = vector_store.search("anything")
        
        assert results.is_empty()
        assert len(results.documents) == 0
        assert len(results.metadata) == 0
        assert results.error is None

    def test_search_results_contain_metadata(self, vector_store: VectorStore):
        """Test that search results include proper metadata."""
        vector_store.add_knowledge_metadata(
            knowledge_id=1,
            title="Test Document",
            uri="file:///test.md",
            category="test",
            tags="tag1"
        )
        
        chunks = [
            TextChunk(
                content="Test content here",
                start_index=0,
                chunk_index=0,
                metadata={
                    "knowledge_id": 1,
                    "title": "Test Document",
                    "uri": "file:///test.md",
                    "category": "test",
                    "chunk_index": 0
                }
            )
        ]
        vector_store.add_knowledge_content(chunks)
        
        results = vector_store.search("test")
        
        assert not results.is_empty()
        meta = results.metadata[0]
        assert meta["knowledge_id"] == 1
        assert meta["title"] == "Test Document"
        assert meta["uri"] == "file:///test.md"
        assert "chunk_index" in meta


class TestVectorStoreRemoval:
    """Tests for removing knowledge items."""

    def test_remove_knowledge_content(self, vector_store: VectorStore):
        """Test removing all chunks for a knowledge item."""
        # Add content
        chunks = [
            TextChunk(
                content=f"Chunk {i}",
                start_index=i * 100,
                chunk_index=i,
                metadata={"knowledge_id": 1, "title": "Doc 1"}
            )
            for i in range(5)
        ]
        vector_store.add_knowledge_content(chunks)
        
        # Verify added
        assert vector_store.knowledge_content.count() == 5
        
        # Remove
        success = vector_store.remove_knowledge_content(1)
        
        assert success is True
        assert vector_store.knowledge_content.count() == 0

    def test_remove_knowledge_content_not_found(self, vector_store: VectorStore):
        """Test removing non-existent knowledge item."""
        success = vector_store.remove_knowledge_content(999)
        assert success is True  # Should succeed even if nothing to remove

    def test_remove_knowledge_metadata(self, vector_store: VectorStore):
        """Test removing knowledge metadata."""
        vector_store.add_knowledge_metadata(
            knowledge_id=1,
            title="To Remove",
            uri="file:///remove.md",
            category="test",
            tags=""
        )
        
        assert vector_store.get_knowledge_count() == 1
        
        success = vector_store.remove_knowledge_metadata(1)
        
        assert success is True
        assert vector_store.get_knowledge_count() == 0

    def test_remove_knowledge_complete(self, vector_store: VectorStore):
        """Test removing both metadata and content."""
        # Add both
        vector_store.add_knowledge_metadata(
            knowledge_id=1,
            title="Complete Doc",
            uri="file:///complete.md",
            category="test",
            tags=""
        )
        chunks = [
            TextChunk(
                content="Content",
                start_index=0,
                chunk_index=0,
                metadata={"knowledge_id": 1, "title": "Complete Doc"}
            )
        ]
        vector_store.add_knowledge_content(chunks)
        
        # Remove both
        vector_store.remove_knowledge_metadata(1)
        vector_store.remove_knowledge_content(1)
        
        assert vector_store.get_knowledge_count() == 0
        assert vector_store.knowledge_content.count() == 0


class TestSearchResults:
    """Tests for SearchResults dataclass."""

    def test_search_results_from_chroma(self):
        """Test creating SearchResults from ChromaDB results."""
        chroma_results = {
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"id": 1}, {"id": 2}]],
            "distances": [[0.1, 0.2]]
        }
        
        results = SearchResults.from_chroma(chroma_results)
        
        assert len(results.documents) == 2
        assert len(results.metadata) == 2
        assert len(results.distances) == 2
        assert results.error is None

    def test_search_results_empty(self):
        """Test creating empty SearchResults with error."""
        results = SearchResults.empty("No results found")
        
        assert results.is_empty()
        assert results.error == "No results found"
        assert len(results.documents) == 0

    def test_search_results_is_empty(self):
        """Test is_empty() method."""
        empty_results = SearchResults(documents=[], metadata=[], distances=[])
        assert empty_results.is_empty()
        
        non_empty = SearchResults(
            documents=["doc"],
            metadata=[{"id": 1}],
            distances=[0.1]
        )
        assert not non_empty.is_empty()


class TestVectorStoreStats:
    """Tests for collection statistics."""

    def test_get_collection_stats(self, vector_store: VectorStore):
        """Test getting statistics about collections."""
        # Add some data
        vector_store.add_knowledge_metadata(
            knowledge_id=1,
            title="Stats Doc",
            uri="file:///stats.md",
            category="test",
            tags=""
        )
        chunks = [
            TextChunk(
                content=f"Chunk {i}",
                start_index=i * 100,
                chunk_index=i,
                metadata={"knowledge_id": 1, "title": "Stats Doc"}
            )
            for i in range(3)
        ]
        vector_store.add_knowledge_content(chunks)
        
        stats = vector_store.get_collection_stats()
        
        assert stats["total_chunks"] == 3
        assert stats["unique_knowledge_items"] == 1
        assert stats["collection_name"] == "knowledge_base_content"  # Default collection name + _content
        assert "embedding_model" in stats

    def test_get_collection_stats_empty(self, vector_store: VectorStore):
        """Test stats for empty collections."""
        stats = vector_store.get_collection_stats()
        
        assert stats["total_chunks"] == 0
        assert stats["unique_knowledge_items"] == 0
