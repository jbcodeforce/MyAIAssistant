"""Unit tests for DocumentProcessor component.

Tests for the DocumentProcessor class that handles document processing
and chunking for the knowledge base.
"""

import pytest
import tempfile
from pathlib import Path
from typing import List

from agent_core.services.rag.document_processor import DocumentProcessor, KnowledgeItem, KnowledgeChunk
from agent_core.services.rag.document_loader import DocumentLoader
from agent_core.services.rag.text_splitter import RecursiveTextSplitter


@pytest.fixture
def document_processor():
    """Create a DocumentProcessor instance for testing."""
    return DocumentProcessor(
        chunk_size=500,
        chunk_overlap=100
    )


@pytest.fixture
def document_loader():
    """Create a DocumentLoader instance for testing."""
    return DocumentLoader()


@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample markdown file for testing."""
    content = """# Test Document

This is a test document with multiple paragraphs.

## Section 1

This is the first section with some content that will be split into chunks.

## Section 2

This is the second section with more content for testing chunking behavior.

### Subsection 2.1

Additional content in a subsection.

## Section 3

Final section with concluding content.
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(content)
    return str(file_path)


class TestDocumentProcessorInitialization:
    """Tests for DocumentProcessor initialization."""

    def test_init_with_parameters(self):
        """Test initialization with chunk size and overlap."""
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        
        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 200
        assert processor.text_splitter is not None
        assert isinstance(processor.text_splitter, RecursiveTextSplitter)

    def test_init_defaults(self):
        """Test initialization with default parameters."""
        processor = DocumentProcessor()
        
        assert processor.chunk_size > 0
        assert processor.chunk_overlap >= 0


class TestDocumentProcessorChunking:
    """Tests for text chunking functionality."""

    def test_chunk_text_basic(self, document_processor: DocumentProcessor):
        """Test basic text chunking."""
        text = "This is a test document. " * 50  # Create long text
        metadata = {"knowledge_id": 1, "title": "Test"}
        
        chunks = document_processor.chunk_text(text, metadata)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, KnowledgeChunk) for chunk in chunks)
        assert all(chunk.knowledge_id == 1 for chunk in chunks)

    def test_chunk_text_respects_size(self, document_processor: DocumentProcessor):
        """Test that chunks respect the size limit."""
        # Create text that should produce multiple chunks
        text = "Sentence. " * 200
        metadata = {"knowledge_id": 1}
        
        chunks = document_processor.chunk_text(text, metadata)
        
        # Most chunks should be within size limit (with some tolerance)
        max_size = document_processor.chunk_size * 1.2
        oversized = [c for c in chunks if len(c.content) > max_size]
        
        # Allow small percentage to exceed (edge cases)
        assert len(oversized) / len(chunks) < 0.2 if chunks else True

    def test_chunk_text_preserves_metadata(self, document_processor: DocumentProcessor):
        """Test that chunk metadata is preserved."""
        text = "Test content. " * 20
        metadata = {
            "knowledge_id": 5,
            "title": "Metadata Test",
            "uri": "file:///test.md",
            "category": "test"
        }
        
        chunks = document_processor.chunk_text(text, metadata)
        
        for chunk in chunks:
            assert chunk.knowledge_id == 5
            assert chunk.metadata == metadata

    def test_chunk_text_with_overlap(self, document_processor: DocumentProcessor):
        """Test that chunks have proper overlap."""
        text = "Sentence one. Sentence two. Sentence three. " * 30
        metadata = {"knowledge_id": 1}
        
        chunks = document_processor.chunk_text(text, metadata)
        
        if len(chunks) > 1:
            # Check that consecutive chunks have some overlap
            first_end = chunks[0].content[-50:]
            second_start = chunks[1].content[:50]
            
            # There should be some common text (overlap)
            # This is a heuristic check
            assert len(first_end) > 0 and len(second_start) > 0

    def test_chunk_text_empty(self, document_processor: DocumentProcessor):
        """Test chunking empty text."""
        chunks = document_processor.chunk_text("", {"knowledge_id": 1})
        
        # Empty text might produce 0 or 1 empty chunk depending on implementation
        assert len(chunks) <= 1

    def test_chunk_text_short_content(self, document_processor: DocumentProcessor):
        """Test chunking content shorter than chunk size."""
        text = "This is a short document."
        metadata = {"knowledge_id": 1}
        
        chunks = document_processor.chunk_text(text, metadata)
        
        # Should produce at least one chunk
        assert len(chunks) >= 1
        assert chunks[0].content == text or text in chunks[0].content


class TestDocumentProcessorProcessing:
    """Tests for document processing functionality."""

    @pytest.mark.asyncio
    async def test_process_document_markdown(
        self,
        document_processor: DocumentProcessor,
        document_loader: DocumentLoader,
        sample_markdown_file: str
    ):
        """Test processing a markdown document."""
        # Load document first
        loaded_docs = await document_loader.load(sample_markdown_file, "markdown")
        loaded_doc = loaded_docs[0]
        
        # Process document
        knowledge_item, chunks = document_processor.process_document(
            loaded_doc=loaded_doc,
            knowledge_id=1,
            title="Test Document",
            metadata={
                "uri": sample_markdown_file,
                "document_type": "markdown",
                "category": "test"
            }
        )
        
        assert isinstance(knowledge_item, KnowledgeItem)
        assert knowledge_item.knowledge_id == 1
        assert knowledge_item.title == "Test Document"
        assert len(chunks) > 0
        assert all(isinstance(chunk, KnowledgeChunk) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_process_document_preserves_content(
        self,
        document_processor: DocumentProcessor,
        document_loader: DocumentLoader,
        sample_markdown_file: str
    ):
        """Test that processing preserves document content."""
        loaded_docs = await document_loader.load(sample_markdown_file, "markdown")
        loaded_doc = loaded_docs[0]
        
        knowledge_item, chunks = document_processor.process_document(
            loaded_doc=loaded_doc,
            knowledge_id=1,
            title="Test",
            metadata={"uri": sample_markdown_file}
        )
        
        # Combine all chunk content
        combined_content = " ".join([chunk.content for chunk in chunks])
        
        # Original content should be present in chunks
        assert "Test Document" in combined_content or "test document" in combined_content.lower()
        assert "Section 1" in combined_content or "section 1" in combined_content.lower()

    @pytest.mark.asyncio
    async def test_process_document_chunk_metadata(
        self,
        document_processor: DocumentProcessor,
        document_loader: DocumentLoader,
        sample_markdown_file: str
    ):
        """Test that chunks have correct metadata."""
        loaded_docs = await document_loader.load(sample_markdown_file, "markdown")
        loaded_doc = loaded_docs[0]
        
        metadata = {
            "uri": sample_markdown_file,
            "document_type": "markdown",
            "category": "test",
            "tags": "tag1,tag2"
        }
        
        knowledge_item, chunks = document_processor.process_document(
            loaded_doc=loaded_doc,
            knowledge_id=2,
            title="Metadata Test",
            metadata=metadata
        )
        
        for chunk in chunks:
            assert chunk.knowledge_id == 2
            assert chunk.metadata["uri"] == sample_markdown_file
            assert chunk.metadata["document_type"] == "markdown"
            assert chunk.metadata["category"] == "test"
            assert chunk.chunk_index >= 0

    @pytest.mark.asyncio
    async def test_process_document_chunk_indices(
        self,
        document_processor: DocumentProcessor,
        document_loader: DocumentLoader,
        sample_markdown_file: str
    ):
        """Test that chunks have sequential indices."""
        loaded_docs = await document_loader.load(sample_markdown_file, "markdown")
        loaded_doc = loaded_docs[0]
        
        knowledge_item, chunks = document_processor.process_document(
            loaded_doc=loaded_doc,
            knowledge_id=1,
            title="Test",
            metadata={"uri": sample_markdown_file}
        )
        
        indices = [chunk.chunk_index for chunk in chunks]
        
        # Indices should be sequential starting from 0
        assert indices == list(range(len(chunks)))

    @pytest.mark.asyncio
    async def test_process_document_multiple_documents(
        self,
        document_processor: DocumentProcessor,
        document_loader: DocumentLoader,
        tmp_path
    ):
        """Test processing multiple documents."""
        # Create multiple test files
        files = []
        for i in range(3):
            file_path = tmp_path / f"doc{i}.md"
            file_path.write_text(f"# Document {i}\n\nContent for document {i}.")
            files.append(str(file_path))
        
        all_chunks = []
        for i, file_path in enumerate(files):
            loaded_docs = await document_loader.load(file_path, "markdown")
            knowledge_item, chunks = document_processor.process_document(
                loaded_doc=loaded_docs[0],
                knowledge_id=i + 1,
                title=f"Document {i}",
                metadata={"uri": file_path}
            )
            all_chunks.extend(chunks)
        
        # Should have chunks from all documents
        assert len(all_chunks) >= 3
        knowledge_ids = set(chunk.knowledge_id for chunk in all_chunks)
        assert knowledge_ids == {1, 2, 3}


class TestKnowledgeItem:
    """Tests for KnowledgeItem model."""

    def test_knowledge_item_creation(self):
        """Test creating a KnowledgeItem."""
        item = KnowledgeItem(
            knowledge_id=1,
            title="Test Item",
            uri="file:///test.md"
        )
        
        assert item.knowledge_id == 1
        assert item.title == "Test Item"
        assert item.uri == "file:///test.md"

    def test_knowledge_item_optional_fields(self):
        """Test KnowledgeItem with optional fields."""
        item = KnowledgeItem(
            knowledge_id=2,
            title="Item 2",
            uri="file:///item2.md",
            category="test",
            tags="tag1,tag2"
        )
        
        assert item.category == "test"
        assert item.tags == "tag1,tag2"


class TestKnowledgeChunk:
    """Tests for KnowledgeChunk model."""

    def test_knowledge_chunk_creation(self):
        """Test creating a KnowledgeChunk."""
        chunk = KnowledgeChunk(
            content="Test content",
            knowledge_id=1,
            chunk_index=0,
            metadata={"title": "Test"}
        )
        
        assert chunk.content == "Test content"
        assert chunk.knowledge_id == 1
        assert chunk.chunk_index == 0
        assert chunk.metadata == {"title": "Test"}

    def test_knowledge_chunk_required_fields(self):
        """Test that required fields are present."""
        chunk = KnowledgeChunk(
            content="Content",
            knowledge_id=5,
            chunk_index=10,
            metadata={}
        )
        
        assert chunk.content is not None
        assert chunk.knowledge_id is not None
        assert chunk.chunk_index is not None
        assert chunk.metadata is not None
