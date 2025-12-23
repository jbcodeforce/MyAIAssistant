"""Document loader for parsing knowledge base sources."""

import hashlib
import re
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify


from pydantic import BaseModel
class LoadedDocument(BaseModel):
    """Represents a loaded document with its content and metadata."""
    content: str
    content_hash: str
    source_uri: str
    title: Optional[str] = None


class DocumentLoader:
    """Loads documents from various sources (markdown files, websites)."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def load(self, uri: str, document_type: str) -> LoadedDocument:
        """
        Load a document from the given URI based on its type.
        
        Args:
            uri: The URI of the document (file path or URL)
            document_type: Type of document ('markdown' or 'website')
            
        Returns:
            LoadedDocument with content and metadata
        """
        if document_type == "markdown":
            return await self._load_markdown(uri)
        elif document_type == "website":
            return await self._load_website(uri)
        else:
            raise ValueError(f"Unsupported document type: {document_type}")

    async def _load_markdown(self, uri: str) -> LoadedDocument:
        """Load a markdown file from a file:// URI or URL."""
        content = ""
        
        if uri.startswith("file://"):
            # Local file
            file_path = uri.replace("file://", "")
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            content = path.read_text(encoding="utf-8")
        elif uri.startswith(("http://", "https://")):
            # Remote markdown file
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(uri)
                response.raise_for_status()
                content = response.text
        else:
            # Assume it's a local path without file:// prefix
            path = Path(uri)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {uri}")
            content = path.read_text(encoding="utf-8")

        # Extract title from markdown (first h1)
        title = self._extract_markdown_title(content)
        
        return LoadedDocument(
            content=content,
            content_hash=self._compute_hash(content),
            source_uri=uri,
            title=title
        )

    async def _load_website(self, uri: str) -> LoadedDocument:
        """Load and extract content from a website."""
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(uri)
            response.raise_for_status()
            html_content = response.text

        # Parse HTML
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Try to find main content area
        main_content = (
            soup.find("main") or 
            soup.find("article") or 
            soup.find("div", class_=re.compile(r"content|main|article", re.I)) or
            soup.find("body")
        )

        if main_content:
            # Convert to markdown for cleaner text
            content = markdownify(str(main_content), heading_style="ATX", strip=["a"])
        else:
            content = soup.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = content.strip()

        # Extract title
        title = None
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)

        return LoadedDocument(
            content=content,
            content_hash=self._compute_hash(content),
            source_uri=uri,
            title=title
        )

    def _extract_markdown_title(self, content: str) -> Optional[str]:
        """Extract the first H1 title from markdown content."""
        # Look for # Title pattern
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content for change detection."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

