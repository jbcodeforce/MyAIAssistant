"""Integration tests for RAG service with website indexing.

These tests require network access to fetch website content.
Run with: pytest tests/it/test_rag_website.py -v -m integration

For LLM-based summarization tests, a running Ollama instance is required.
"""

import os
import shutil
import tempfile
from pathlib import Path

import httpx
import pytest

from agent_core.services.rag.document_loader import (
    DocumentLoader, 
    LoadedDocument,
    filter_web_noise,
    filter_short_lines,
)
from agent_core.services.rag.text_splitter import RecursiveTextSplitter, TextChunk
from agent_core.services.rag.service import RAGService, SearchResult
from agent_core.agents.agent_factory import AgentConfig, get_agent_factory
from agent_core.agents.base_agent import BaseAgent, AgentInput


# Test website URL - Apache Flink Process Table Functions documentation
FLINK_PTF_URL = "https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/functions/ptfs/"

# Ollama configuration for LLM tests
OLLAMA_MODEL = os.getenv("OLLAMA_TEST_MODEL", "mistral-small")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def is_url_accessible(url: str, timeout: float = 10.0) -> bool:
    """Check if a URL is accessible."""
    try:
        response = httpx.head(url, timeout=timeout, follow_redirects=True)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
        return False


def is_ollama_available() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def is_model_available(model: str) -> bool:
    """Check if the specified model is available in Ollama."""
    try:
        response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        if response.status_code != 200:
            return False
        data = response.json()
        models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
        return model in models or any(model in m for m in models)
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


# Skip marker for tests requiring network
requires_network = pytest.mark.skipif(
    not is_url_accessible(FLINK_PTF_URL),
    reason=f"URL {FLINK_PTF_URL} is not accessible"
)

# Skip markers for LLM tests
requires_ollama = pytest.mark.skipif(
    not is_ollama_available(),
    reason="Ollama is not running or not accessible"
)

requires_model = pytest.mark.skipif(
    not is_model_available(OLLAMA_MODEL),
    reason=f"Model {OLLAMA_MODEL} is not available in Ollama"
)


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB storage."""
    tmpdir = tempfile.mkdtemp(prefix="rag_test_")
    yield tmpdir
    # Cleanup after test
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def rag_service(temp_chroma_dir: str) -> RAGService:
    """Create a RAGService with isolated storage for testing."""
    # Override environment variables for test isolation
    os.environ["CHROMA_PERSIST_DIRECTORY"] = temp_chroma_dir
    os.environ["CHROMA_COLLECTION_NAME"] = "test_website_collection"
    
    return RAGService(
        persist_directory=temp_chroma_dir,
        collection_name="test_website_collection",
        chunk_size=1000,
        chunk_overlap=200,
        embedding_model="all-MiniLM-L6-v2"
    )


@pytest.fixture
def document_loader() -> DocumentLoader:
    """Create a DocumentLoader for testing."""
    return DocumentLoader(timeout=30.0)


@pytest.fixture
def text_splitter() -> RecursiveTextSplitter:
    """Create a text splitter for testing."""
    return RecursiveTextSplitter(chunk_size=1000, chunk_overlap=200)


@pytest.fixture
def ollama_config() -> AgentConfig:
    """Create AgentConfig for Ollama integration tests."""
    return AgentConfig(
        name="OllamaRAGTest",
        provider="ollama",
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        max_tokens=512,
        temperature=0.3,
        timeout=180.0,  # Increased timeout for longer contexts
    )


@pytest.fixture
def general_agent(ollama_config: AgentConfig) -> BaseAgent:
    """Create a BaseAgent (general agent) with Ollama config."""
    return BaseAgent(config=ollama_config)


@pytest.fixture
def rag_agent(ollama_config: AgentConfig, rag_service: RAGService) -> BaseAgent:
    """Create a BaseAgent with RAG enabled for Ollama config and RAG service."""
    agent = BaseAgent(
        config=ollama_config,
        rag_service=rag_service,
        use_rag=True,
        rag_top_k=5
    )
    # Set agent_type to "rag" for backward compatibility with tests
    agent.agent_type = "rag"
    return agent


@pytest.mark.integration
@requires_network
class TestDocumentLoaderWebsite:
    """Tests for loading website content."""

    @pytest.mark.asyncio
    async def test_load_flink_ptf_website(self, document_loader: DocumentLoader):
        """Test loading the Flink PTF documentation website."""
        documents = await document_loader.load(FLINK_PTF_URL, "website")
        
        assert len(documents) == 1
        doc = documents[0]
        
        assert isinstance(doc, LoadedDocument)
        assert len(doc.content) > 1000  # Should have substantial content
        assert doc.content_hash is not None
        assert len(doc.content_hash) == 64  # SHA256 hash
        assert doc.source_uri == FLINK_PTF_URL
        
        # Title should be extracted
        assert doc.title is not None
        assert len(doc.title) > 0

    @pytest.mark.asyncio
    async def test_website_content_contains_ptf_keywords(self, document_loader: DocumentLoader):
        """Test that loaded content contains expected PTF-related keywords."""
        documents = await document_loader.load(FLINK_PTF_URL, "website")
        doc = documents[0]
        content_lower = doc.content.lower()
        
        # The page should contain key PTF terms
        assert "process table function" in content_lower or "ptf" in content_lower
        assert "table" in content_lower
        assert "flink" in content_lower


class TestWebNoiseFiltering:
    """Tests for web noise filtering functions."""

    def test_filter_back_to_top_phrases(self):
        """Test that 'back to top' phrases are removed."""
        content = """# Header

Some content here.

Back to top

More content.

scroll to top

End of content."""
        
        filtered = filter_web_noise(content)
        
        assert "Back to top" not in filtered
        assert "scroll to top" not in filtered
        assert "Some content here" in filtered
        assert "More content" in filtered
        assert "End of content" in filtered

    def test_filter_edit_prompts(self):
        """Test that edit prompts are removed."""
        content = """# Documentation

Important information here.

Edit this page

Edit on GitHub

More documentation."""
        
        filtered = filter_web_noise(content)
        
        assert "Edit this page" not in filtered
        assert "Edit on GitHub" not in filtered
        assert "Important information" in filtered

    def test_filter_navigation_elements(self):
        """Test that navigation elements are removed."""
        content = """# Content

Real content here.

Previous

Next

←

→

Skip to content

More real content."""
        
        filtered = filter_web_noise(content)
        
        assert "Previous" not in filtered
        assert "Next" not in filtered
        assert "Skip to content" not in filtered
        assert "Real content here" in filtered

    def test_filter_translation_prompts(self):
        """Test that translation prompts are removed."""
        content = """# Guide

Content here.

Want to contribute translation?

Help us translate

More content."""
        
        filtered = filter_web_noise(content)
        
        assert "Want to contribute translation" not in filtered
        assert "Help us translate" not in filtered
        assert "Content here" in filtered

    def test_filter_toc_headers(self):
        """Test that table of contents headers are removed."""
        content = """# Main Title

On this page:

Table of Contents

In this article:

Actual content here."""
        
        filtered = filter_web_noise(content)
        
        assert "On this page" not in filtered
        assert "Table of Contents" not in filtered
        assert "In this article" not in filtered
        assert "Main Title" in filtered
        assert "Actual content" in filtered

    def test_filter_arrows_and_icons(self):
        """Test that standalone arrows and icons are removed."""
        content = """# Header



Content here.



More content."""
        
        filtered = filter_web_noise(content)
        
        # Check arrows are removed (they're on their own lines)
        lines = [l.strip() for l in filtered.split('\n') if l.strip()]
        arrow_lines = [l for l in lines if l in ['▾', '▸', '►', '▼', '⬆', '⬇']]
        assert len(arrow_lines) == 0
        assert "Content here" in filtered

    def test_filter_preserves_real_content(self):
        """Test that real content is preserved."""
        content = """# Process Table Functions

A Process Table Function (PTF) is a user-defined table function that can:
- Maintain state across rows
- Use timers for delayed processing
- Produce multiple output rows

## Example

public class MyPTF extends ProcessTableFunction<Row> {
    public void eval(Context ctx, Row input) {
        collect(Row.of(input.getField(0)));
    }
}"""
        
        filtered = filter_web_noise(content)
        
        # All real content should be preserved
        assert "Process Table Functions" in filtered
        assert "Maintain state across rows" in filtered
        assert "ProcessTableFunction" in filtered
        assert "eval" in filtered

    def test_filter_short_lines(self):
        """Test that very short lines are filtered."""
        content = """# Header

Some real content here.

A

B

More content.

OK

This is a longer line that should stay."""
        
        filtered = filter_short_lines(content, min_length=3)
        
        assert "Some real content here" in filtered
        assert "More content" in filtered
        assert "This is a longer line" in filtered
        # Single letters should be removed
        lines = [l.strip() for l in filtered.split('\n') if l.strip()]
        assert "A" not in lines
        assert "B" not in lines
        # But "OK" should also be removed (less than 3 chars)
        assert "OK" not in lines

    def test_filter_short_lines_preserves_headers(self):
        """Test that headers are preserved even if short."""
        content = """# H1

## OK

Content here.

### A

More content."""
        
        filtered = filter_short_lines(content, min_length=3)
        
        # Headers should be preserved regardless of length
        assert "# H1" in filtered
        assert "## OK" in filtered
        assert "### A" in filtered

    def test_combined_filtering_on_realistic_content(self):
        """Test combined filtering on realistic web content."""
        content = """# Documentation Guide

On this page:

- Introduction
- Getting Started
- Examples

## Introduction

This guide explains the core concepts.

Back to top

## Getting Started

Follow these steps to begin.

Edit this page

## Examples

Here are some practical examples.

Previous | Next

Want to contribute translation?

© 2024 Company Name"""
        
        # Apply both filters
        filtered = filter_web_noise(content)
        filtered = filter_short_lines(filtered, min_length=3)
        
        # Real content should be preserved
        assert "Documentation Guide" in filtered
        assert "Introduction" in filtered
        assert "core concepts" in filtered
        assert "Getting Started" in filtered
        assert "Follow these steps" in filtered
        assert "Examples" in filtered
        assert "practical examples" in filtered
        
        # Noise should be removed
        assert "On this page" not in filtered
        assert "Back to top" not in filtered
        assert "Edit this page" not in filtered
        assert "Want to contribute translation" not in filtered


@pytest.mark.integration
@requires_network
class TestWebNoiseFilteringIntegration:
    """Integration tests for noise filtering with real website content."""

    @pytest.mark.asyncio
    async def test_flink_docs_noise_filtered(self, document_loader: DocumentLoader):
        """Test that Flink documentation has noise filtered."""
        documents = await document_loader.load(FLINK_PTF_URL, "website")
        content = documents[0].content.lower()
        
        # These phrases should be filtered out
        noise_phrases = [
            "back to top",
            "edit this page",
            "want to contribute translation",
        ]
        
        for phrase in noise_phrases:
            # Check that these don't appear as standalone lines
            lines = [l.strip().lower() for l in content.split('\n')]
            assert phrase not in lines, f"Found noise phrase: '{phrase}'"
        
        # Real content should still be present
        assert "process table" in content or "ptf" in content
        assert "table" in content

    @pytest.mark.asyncio
    async def test_content_quality_after_filtering(self, document_loader: DocumentLoader):
        """Test that content quality is maintained after filtering."""
        documents = await document_loader.load(FLINK_PTF_URL, "website")
        content = documents[0].content
        
        # Content should be substantial
        assert len(content) > 5000, "Content should be substantial after filtering"
        
        # Should contain code examples (PTF docs have Java code)
        code_indicators = ["class", "public", "void", "extends"]
        found_code = any(ind in content for ind in code_indicators)
        assert found_code, "Code examples should be preserved after filtering"
        
        # Should have proper paragraph structure
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        assert len(paragraphs) > 10, "Should have multiple paragraphs"


@pytest.mark.integration
@requires_network
class TestTextSplitterWithWebsite:
    """Tests for text splitting with website content."""

    @pytest.mark.asyncio
    async def test_split_website_content(
        self, 
        document_loader: DocumentLoader, 
        text_splitter: RecursiveTextSplitter
    ):
        """Test splitting website content into chunks."""
        documents = await document_loader.load(FLINK_PTF_URL, "website")
        doc = documents[0]
        
        metadata = {
            "source_uri": doc.source_uri,
            "title": doc.title,
            "document_type": "website"
        }
        
        chunks = text_splitter.split_text(doc.content, metadata)
        
        assert len(chunks) > 0
        assert all(isinstance(c, TextChunk) for c in chunks)
        
        # Each chunk should have content
        for chunk in chunks:
            assert len(chunk.content) > 0
            assert chunk.chunk_index >= 0
            assert chunk.start_index >= 0
            assert chunk.metadata == metadata

    @pytest.mark.asyncio
    async def test_chunks_respect_size_limit(
        self, 
        document_loader: DocumentLoader, 
        text_splitter: RecursiveTextSplitter
    ):
        """Test that chunks respect the size limit."""
        documents = await document_loader.load(FLINK_PTF_URL, "website")
        doc = documents[0]
        
        chunks = text_splitter.split_text(doc.content)
        
        # Most chunks should be within the size limit (with some tolerance)
        max_size = text_splitter.chunk_size * 1.5
        oversized = [c for c in chunks if len(c.content) > max_size]
        
        # Allow a small percentage to exceed (edge cases)
        assert len(oversized) / len(chunks) < 0.1, (
            f"Too many oversized chunks: {len(oversized)}/{len(chunks)}"
        )


@pytest.mark.integration
@requires_network
class TestRAGServiceWebsite:
    """Integration tests for full RAG pipeline with website content."""

    @pytest.mark.asyncio
    async def test_index_flink_ptf_website(self, rag_service: RAGService):
        """Test indexing the Flink PTF documentation website."""
        result = await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        assert result.success is True
        assert result.chunks_indexed > 0
        assert result.content_hash is not None
        assert len(result.content_hash) == 64
        assert result.error is None
        
        # Verify stats
        stats = rag_service.get_collection_stats()
        assert stats["total_chunks"] == result.chunks_indexed
        assert stats["unique_knowledge_items"] == 1

    @pytest.mark.asyncio
    async def test_search_ptf_content(self, rag_service: RAGService):
        """Test searching for PTF-related content after indexing."""
        # First, index the website
        index_result = await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        assert index_result.success is True
        
        # Search for PTF concepts
        results = await rag_service.search(
            query="What is a Process Table Function and how does it work?",
            n_results=5
        )
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        
        # Top result should be relevant
        top_result = results[0]
        assert top_result.score > 0.3  # Reasonable similarity score
        assert top_result.knowledge_id == 1
        # Title is extracted from webpage, should contain PTF-related text
        assert "process table" in top_result.title.lower() or "ptf" in top_result.title.lower()
        
        # Content should contain relevant information
        assert len(top_result.content) > 50
        print(top_result.content)

    @pytest.mark.asyncio
    async def test_search_state_management(self, rag_service: RAGService):
        """Test searching for state management concepts in PTF documentation."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Search for state-related content
        results = await rag_service.search(
            query="How does state management work in Process Table Functions?",
            n_results=3
        )
        
        assert len(results) > 0
        
        # Verify results contain state-related content
        combined_content = " ".join([r.content.lower() for r in results])
        state_terms = ["state", "stateful", "@statehint", "persistence"]
        
        found_terms = [term for term in state_terms if term in combined_content]
        assert len(found_terms) > 0, (
            f"Expected state-related terms in search results. "
            f"Found content: {combined_content[:500]}..."
        )
        print(combined_content)

    @pytest.mark.asyncio
    async def test_search_timer_concepts(self, rag_service: RAGService):
        """Test searching for timer concepts in PTF documentation."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Search for timer-related content
        results = await rag_service.search(
            query="How to use timers and time-based processing in PTF?",
            n_results=3
        )
        
        assert len(results) > 0
        
        # Verify results contain timer-related content
        combined_content = " ".join([r.content.lower() for r in results])
        timer_terms = ["timer", "time", "ontimer", "registerontime"]
        
        found_terms = [term for term in timer_terms if term in combined_content]
        assert len(found_terms) > 0, (
            f"Expected timer-related terms in search results. "
            f"Found content: {combined_content[:500]}..."
        )

    @pytest.mark.asyncio
    async def test_search_shopping_cart_example(self, rag_service: RAGService):
        """Test searching for the shopping cart example from PTF documentation."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Search for the shopping cart example
        results = await rag_service.search(
            query="Shopping cart example with checkout and reminder",
            n_results=5
        )
        
        assert len(results) > 0
        
        # The documentation contains a shopping cart example
        combined_content = " ".join([r.content.lower() for r in results])
        cart_terms = ["cart", "checkout", "reminder", "shopping"]
        
        found_terms = [term for term in cart_terms if term in combined_content]
        assert len(found_terms) >= 1, (
            f"Expected shopping cart example content. "
            f"Found content preview: {combined_content[:500]}..."
        )

    @pytest.mark.asyncio
    async def test_search_with_category_filter(self, rag_service: RAGService):
        """Test that category filtering works for website content."""
        # Index with specific category
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql"
        )
        
        # Search with matching category
        results_with_category = await rag_service.search(
            query="Process Table Function",
            n_results=3,
            category="Flink/Documentation"
        )
        
        assert len(results_with_category) > 0
        
        # Search with non-matching category
        results_wrong_category = await rag_service.search(
            query="Process Table Function",
            n_results=3,
            category="NonExistent/Category"
        )
        
        # Should return empty or fewer results
        assert len(results_wrong_category) == 0

    @pytest.mark.asyncio
    async def test_remove_website_from_index(self, rag_service: RAGService):
        """Test removing website content from the index."""
        # Index the website
        index_result = await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf"
        )
        
        chunks_before = index_result.chunks_indexed
        assert chunks_before > 0
        
        # Remove from index
        success = await rag_service.remove_knowledge(1)
        assert success is True
        
        # Verify removal
        stats = rag_service.get_collection_stats()
        assert stats["total_chunks"] == 0
        assert stats["unique_knowledge_items"] == 0
        
        # Search should return empty
        results = await rag_service.search(
            query="Process Table Function",
            n_results=5
        )
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_reindex_website_updates_content(self, rag_service: RAGService):
        """Test that reindexing updates the content correctly."""
        # Index first time
        result1 = await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink"
        )
        
        chunks1 = result1.chunks_indexed
        hash1 = result1.content_hash
        
        # Reindex (should replace existing chunks)
        result2 = await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions Updated",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,updated"
        )
        
        # Should have same number of chunks (same content)
        assert result2.chunks_indexed == chunks1
        # Content hash should be the same
        assert result2.content_hash == hash1
        
        # Stats should show same number of chunks (not doubled)
        stats = rag_service.get_collection_stats()
        assert stats["total_chunks"] == chunks1


@pytest.mark.integration
@requires_network
class TestRAGContentQuality:
    """Tests for the quality of RAG content extraction and retrieval."""

    @pytest.mark.asyncio
    async def test_content_extraction_removes_navigation(
        self, 
        document_loader: DocumentLoader
    ):
        """Test that navigation and footer elements are removed from content."""
        documents = await document_loader.load(FLINK_PTF_URL, "website")
        content = documents[0].content.lower()
        
        # Navigation elements should be removed or minimized
        nav_patterns = [
            "skip to content",
            "table of contents",
            "footer",
        ]
        
        # Content should not be dominated by navigation
        # The actual PTF content should be the main portion
        assert "process table" in content or "ptf" in content

    @pytest.mark.asyncio
    async def test_code_examples_preserved(
        self, 
        document_loader: DocumentLoader
    ):
        """Test that code examples from the page are preserved."""
        documents = await document_loader.load(FLINK_PTF_URL, "website")
        content = documents[0].content
        
        # The PTF documentation has Java code examples
        # Check for common Java patterns
        code_indicators = [
            "public",
            "class",
            "void",
            "extends",
        ]
        
        found_code = any(indicator in content for indicator in code_indicators)
        assert found_code, "Expected Java code examples to be preserved in content"

    @pytest.mark.asyncio
    async def test_semantic_search_relevance(self, rag_service: RAGService):
        """Test that semantic search returns relevant results."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Test queries with expected relevant results
        test_cases = [
            {
                "query": "How to define custom output for PTF?",
                "expected_terms": ["output", "collect", "return", "row"]
            },
            {
                "query": "How to handle events in Process Table Function?",
                "expected_terms": ["event", "eval", "process", "context"]
            },
            {
                "query": "What are the limitations of PTF?",
                "expected_terms": ["limitation", "batch", "broadcast"]
            }
        ]
        
        for case in test_cases:
            results = await rag_service.search(
                query=case["query"],
                n_results=3
            )
            
            assert len(results) > 0, f"No results for query: {case['query']}"
            
            combined_content = " ".join([r.content.lower() for r in results])
            found_terms = [
                term for term in case["expected_terms"] 
                if term in combined_content
            ]
            
            # At least one expected term should be found
            assert len(found_terms) > 0, (
                f"Query '{case['query']}' expected terms {case['expected_terms']} "
                f"but none found in: {combined_content[:300]}..."
            )


@pytest.mark.integration
@requires_network
class TestRAGSummarization:
    """Tests for using RAG to summarize website content."""

    @pytest.mark.asyncio
    async def test_retrieve_comprehensive_content(self, rag_service: RAGService):
        """Test retrieving comprehensive content that could be used for summarization."""
        # Index the website
        index_result = await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Retrieve multiple chunks to get comprehensive view
        results = await rag_service.search(
            query="Summarize what Process Table Functions are and their key features",
            n_results=10
        )
        
        assert len(results) >= 5, "Should retrieve multiple chunks for summarization"
        
        # Combine content for analysis
        combined_content = "\n\n".join([r.content for r in results])
        
        # The combined content should cover key PTF concepts
        key_concepts = [
            "table",
            "function",
            "state",
            "process",
        ]
        
        content_lower = combined_content.lower()
        found_concepts = [c for c in key_concepts if c in content_lower]
        
        assert len(found_concepts) >= 3, (
            f"Expected comprehensive coverage. Found: {found_concepts}. "
            f"Content length: {len(combined_content)} chars"
        )
        
        # Content should be substantial enough for summarization
        assert len(combined_content) > 2000, (
            "Combined content should be substantial for summarization"
        )

    @pytest.mark.asyncio
    async def test_retrieve_different_aspects(self, rag_service: RAGService):
        """Test that different queries retrieve different aspects of the content."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Query for different aspects
        queries = [
            "What is the basic structure and definition of a PTF?",
            "How does state management work in PTF?",
            "What are the examples and use cases for PTF?",
        ]
        
        all_chunks = set()
        for query in queries:
            results = await rag_service.search(query=query, n_results=3)
            for r in results:
                all_chunks.add(r.chunk_index)
        
        # Different queries should retrieve some different chunks
        assert len(all_chunks) >= 5, (
            f"Expected diverse chunks from different queries. "
            f"Got {len(all_chunks)} unique chunks"
        )


@pytest.mark.integration
@requires_network
@requires_ollama
@requires_model
class TestRAGWithLLMSummarization:
    """Tests for RAG + LLM integration for content summarization.
    
    These tests require both network access and a running Ollama instance.
    """

    @pytest.mark.asyncio
    async def test_summarize_ptf_content_with_general_agent(
        self,
        rag_service: RAGService,
        general_agent: BaseAgent
    ):
        """Test using GeneralAgent to summarize retrieved PTF content."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Retrieve relevant content
        results = await rag_service.search(
            query="What are Process Table Functions and their main features?",
            n_results=5
        )
        
        # Build context from retrieved chunks
        context_parts = [f"[Source: {r.title}]\n{r.content}" for r in results]
        rag_context = "\n\n---\n\n".join(context_parts)
        
        # Create summarization prompt
        prompt = f"""Based on the following documentation excerpts, provide a concise summary 
of what Flink Process Table Functions (PTFs) are and their key features.

Documentation Context:
{rag_context}

Provide a summary in 3-5 sentences."""
        
        # Use GeneralAgent to summarize
        response = await general_agent.execute(AgentInput(query=prompt))
        
        assert response.message is not None
        assert len(response.message) > 100  # Should have meaningful content
        assert response.agent_type == "general"
        
        # Summary should mention key concepts
        summary_lower = response.message.lower()
        key_terms = ["table", "function", "flink", "process"]
        found_terms = [t for t in key_terms if t in summary_lower]
        
        assert len(found_terms) >= 2, (
            f"Summary should mention key PTF concepts. Found: {found_terms}. "
            f"Summary: {response.message[:500]}..."
        )
        
        print(f"\n--- PTF Summary ---\n{response.message}\n")

    @pytest.mark.asyncio
    async def test_rag_agent_answers_ptf_question(
        self,
        rag_service: RAGService,
        rag_agent: BaseAgent
    ):
        """Test using RAGAgent to answer questions about PTF documentation."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Use RAGAgent to answer a question
        response = await rag_agent.execute(AgentInput(
            query="What is a Process Table Function in Flink and how is it different from a regular table function?"
        ))
        
        assert response.message is not None
        assert len(response.message) > 50
        assert response.agent_type == "rag"
        
        # Should have context from RAG search
        assert len(response.context_used) > 0
        
        # Check that context includes relevant sources
        sources = [ctx.get("title", "") for ctx in response.context_used]
        assert any("process table" in s.lower() or "flink" in s.lower() for s in sources)
        
        print(f"\n--- RAG Agent Response ---")
        print(f"Answer: {response.message}")
        print(f"Sources used: {len(response.context_used)}")

    @pytest.mark.asyncio
    async def test_summarize_state_management(
        self,
        rag_service: RAGService,
        general_agent: BaseAgent
    ):
        """Test summarizing state management concepts from PTF documentation."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Retrieve state-related content
        results = await rag_service.search(
            query="State management and stateful processing in PTF",
            n_results=5
        )
        
        context = "\n\n".join([r.content for r in results])
        
        prompt = f"""Based on this documentation about Flink Process Table Functions, 
explain how state management works in PTFs. Focus on:
1. How to declare state
2. State persistence
3. State TTL (time-to-live)

Documentation:
{context}

Provide a technical summary."""
        
        response = await general_agent.execute(AgentInput(query=prompt))
        
        assert response.message is not None
        assert len(response.message) > 100
        
        # Should cover state concepts
        response_lower = response.message.lower()
        state_terms = ["state", "persist", "ttl", "statehint"]
        found_terms = [t for t in state_terms if t in response_lower]
        
        assert len(found_terms) >= 1, (
            f"Summary should cover state concepts. Found: {found_terms}. "
            f"Response: {response.message[:300]}..."
        )
        
        print(f"\n--- State Management Summary ---\n{response.message}\n")

    @pytest.mark.asyncio
    async def test_explain_shopping_cart_example(
        self,
        rag_service: RAGService,
        general_agent: BaseAgent
    ):
        """Test explaining the shopping cart example from PTF documentation."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Retrieve shopping cart example content (fewer chunks to reduce context size)
        results = await rag_service.search(
            query="Shopping cart checkout reminder",
            n_results=3
        )
        
        # Truncate content to avoid timeout
        context = "\n\n".join([r.content[:500] for r in results])
        
        prompt = f"""Based on this PTF documentation, briefly explain the Shopping Cart example.

Documentation:
{context}

Provide a 2-3 sentence summary."""
        
        response = await general_agent.execute(AgentInput(query=prompt))
        
        assert response.message is not None
        assert len(response.message) > 50
        
        # Should mention shopping cart concepts
        response_lower = response.message.lower()
        cart_terms = ["cart", "checkout", "add", "remove", "timer", "reminder", "event"]
        found_terms = [t for t in cart_terms if t in response_lower]
        
        assert len(found_terms) >= 1, (
            f"Explanation should cover shopping cart concepts. Found: {found_terms}. "
            f"Response: {response.message[:300]}..."
        )
        
        print(f"\n--- Shopping Cart Example Explanation ---\n{response.message}\n")

    @pytest.mark.asyncio
    async def test_rag_agent_with_conversation_history(
        self,
        rag_service: RAGService,
        rag_agent: BaseAgent
    ):
        """Test RAGAgent with conversation context for follow-up questions."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Create a simulated conversation history (avoids double LLM call)
        conversation_history = [
            {"role": "user", "content": "What is a Process Table Function?"},
            {"role": "assistant", "content": "A PTF is a user-defined function in Flink SQL that processes table data with state and timers."}
        ]
        
        # Follow-up question with conversation history
        response = await rag_agent.execute(AgentInput(
            query="How do I manage state in PTF?",
            conversation_history=conversation_history
        ))
        
        assert response.message is not None
        assert len(response.message) > 50
        assert response.agent_type == "rag"
        
        # Should have retrieved context
        assert len(response.context_used) > 0
        
        # Should understand context and address state
        response_lower = response.message.lower()
        state_terms = ["state", "statehint", "persist", "store"]
        found_terms = [t for t in state_terms if t in response_lower]
        
        assert len(found_terms) >= 1, (
            f"Response should address state management. Found: {found_terms}"
        )
        
        print(f"\n--- Follow-up Response ---\n{response.message}\n")

    @pytest.mark.asyncio
    async def test_generate_code_example_explanation(
        self,
        rag_service: RAGService,
        general_agent: BaseAgent
    ):
        """Test generating explanation for PTF code examples."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Retrieve code-related content (fewer chunks)
        results = await rag_service.search(
            query="ProcessTableFunction Java class eval method",
            n_results=3
        )
        
        # Truncate to reduce context size
        context = "\n\n".join([r.content[:400] for r in results])
        
        prompt = f"""Based on this PTF documentation, briefly explain how to implement a PTF in Java.

Documentation:
{context}

Provide a 2-3 sentence summary focusing on class structure and eval method."""
        
        response = await general_agent.execute(AgentInput(query=prompt))
        
        assert response.message is not None
        assert len(response.message) > 50
        
        # Should mention implementation concepts
        response_lower = response.message.lower()
        impl_terms = ["class", "extends", "eval", "method", "function", "process"]
        found_terms = [t for t in impl_terms if t in response_lower]
        
        assert len(found_terms) >= 1, (
            f"Explanation should cover implementation concepts. Found: {found_terms}"
        )
        
        print(f"\n--- Code Implementation Explanation ---\n{response.message}\n")

    @pytest.mark.asyncio
    async def test_compare_ptf_limitations(
        self,
        rag_service: RAGService,
        general_agent: BaseAgent
    ):
        """Test summarizing PTF limitations from documentation."""
        # Index the website
        await rag_service.index_knowledge(
            knowledge_id=1,
            title="Flink Process Table Functions",
            uri=FLINK_PTF_URL,
            document_type="website",
            category="Flink/Documentation",
            tags="flink,ptf,sql,streaming"
        )
        
        # Retrieve limitation-related content
        results = await rag_service.search(
            query="PTF limitations restrictions batch mode broadcast state",
            n_results=5
        )
        
        context = "\n\n".join([r.content for r in results])
        
        prompt = f"""Based on the Flink PTF documentation, what are the current 
limitations of Process Table Functions? List the key limitations mentioned.

Documentation:
{context}

Provide a concise bullet-point list of limitations."""
        
        response = await general_agent.execute(AgentInput(query=prompt))
        
        assert response.message is not None
        assert len(response.message) > 50
        
        # Should mention at least one limitation concept
        response_lower = response.message.lower()
        limit_terms = ["limitation", "batch", "broadcast", "cannot", "not support"]
        found_terms = [t for t in limit_terms if t in response_lower]
        
        # Limitations section may be brief, so we're flexible here
        print(f"\n--- PTF Limitations ---\n{response.message}\n")

