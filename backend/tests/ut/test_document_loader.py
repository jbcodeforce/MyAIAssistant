"""Unit tests for DocumentLoader class."""

import pytest
import tempfile
import os
from pathlib import Path

from app.rag.document_loader import DocumentLoader, LoadedDocument


# Path to test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "src_docs"


class TestLoadDirectory:
    """Tests for the _load_directory method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = DocumentLoader()

    def test_load_directory_returns_list_of_documents(self):
        """Test that _load_directory returns a list of LoadedDocument objects."""
        print(f"TEST_DATA_DIR: {TEST_DATA_DIR}")
        documents = self.loader._load_directory(str(TEST_DATA_DIR))
        
        assert isinstance(documents, list)
        assert len(documents) > 0
        for doc in documents:
            assert isinstance(doc, LoadedDocument)

    def test_load_directory_excludes_readme(self):
        """Test that README.md files are excluded from loading."""
        documents = self.loader._load_directory(str(TEST_DATA_DIR))
        
        filenames = [doc.document_id for doc in documents]
        # README.md should not be in the list
        assert "README.md" not in filenames
        assert not any("readme" in f.lower() for f in filenames if "README" in f)

    def test_load_directory_parses_frontmatter(self):
        """Test that documents with frontmatter have metadata extracted."""
        documents = self.loader._load_directory(str(TEST_DATA_DIR))
        
        # Find the document with frontmatter
        frontmatter_doc = next(
            (d for d in documents if d.document_id == "frontmatter_doc_001"),
            None
        )
        
        assert frontmatter_doc is not None
        assert frontmatter_doc.title == "Test Document With Frontmatter"
        assert frontmatter_doc.source_uri == "https://example.com/frontmatter-doc"

    def test_load_directory_extracts_title_from_h1(self):
        """Test that documents without frontmatter extract title from H1."""
        documents = self.loader._load_directory(str(TEST_DATA_DIR))
        
        # Find the simple document (no frontmatter)
        simple_doc = next(
            (d for d in documents if d.document_id == "simple_doc.md"),
            None
        )
        
        assert simple_doc is not None
        assert simple_doc.title == "Simple Document"

    def test_load_directory_generates_content_hash(self):
        """Test that each document has a content hash."""
        documents = self.loader._load_directory(str(TEST_DATA_DIR))
        
        for doc in documents:
            assert doc.content_hash is not None
            assert len(doc.content_hash) == 64  # SHA256 hash length

    def test_load_directory_nonexistent_raises_error(self):
        """Test that loading a non-existent directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            self.loader._load_directory("/nonexistent/path/to/directory")

    def test_load_directory_empty_returns_empty_list(self):
        """Test that loading an empty directory returns an empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            documents = self.loader._load_directory(tmpdir)
            assert documents == []

    def test_load_directory_only_processes_md_files(self):
        """Test that only .md files are processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a markdown file
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("# Test\n\nContent")
            
            # Create a non-markdown file
            txt_file = Path(tmpdir) / "test.txt"
            txt_file.write_text("This should be ignored")
            
            # Create another non-markdown file
            json_file = Path(tmpdir) / "config.json"
            json_file.write_text('{"key": "value"}')
            
            documents = self.loader._load_directory(tmpdir)
            
            assert len(documents) == 1
            assert documents[0].title == "Test"

    def test_load_directory_document_content_not_empty(self):
        """Test that loaded documents have non-empty content."""
        documents = self.loader._load_directory(str(TEST_DATA_DIR))
        
        for doc in documents:
            assert doc.content is not None
            assert len(doc.content.strip()) > 0

    def test_load_directory_uses_filename_as_document_id_without_frontmatter(self):
        """Test that document_id defaults to filename when no frontmatter."""
        documents = self.loader._load_directory(str(TEST_DATA_DIR))
        
        # Simple doc should use filename as document_id
        simple_doc = next(
            (d for d in documents if d.document_id == "simple_doc.md"),
            None
        )
        assert simple_doc is not None

    def test_load_directory_handles_partial_frontmatter(self):
        """Test handling of frontmatter with only some fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with partial frontmatter (only title)
            partial_file = Path(tmpdir) / "partial.md"
            partial_file.write_text("""---
title: Partial Frontmatter Doc
---

# Content Title

Some content here.
""")
            
            documents = self.loader._load_directory(tmpdir)
            
            assert len(documents) == 1
            doc = documents[0]
            assert doc.title == "Partial Frontmatter Doc"
            # document_id should use the file name since it's not in frontmatter
            assert doc.document_id == "partial.md"


class TestLoadDirectoryViaLoadMethod:
    """Tests for _load_directory accessed via the public load() method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = DocumentLoader()

    @pytest.mark.asyncio
    async def test_load_with_folder_type(self):
        """Test that load() with 'folder' type calls _load_directory."""
        documents = await self.loader.load(str(TEST_DATA_DIR), "folder")
        
        assert isinstance(documents, list)
        assert len(documents) > 0
        for doc in documents:
            assert isinstance(doc, LoadedDocument)

    @pytest.mark.asyncio
    async def test_load_folder_excludes_readme(self):
        """Test that folder loading via load() excludes README.md."""
        documents = await self.loader.load(str(TEST_DATA_DIR), "folder")
        
        document_ids = [doc.document_id for doc in documents]
        assert "README.md" not in document_ids

