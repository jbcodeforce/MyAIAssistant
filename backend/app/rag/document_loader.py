"""Document loader for parsing knowledge base sources."""

from ast import List
import hashlib
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify


from pydantic import BaseModel
class LoadedDocument(BaseModel):
    """Represents a loaded document with its content and metadata."""
    content: str
    document_id: str 
    content_hash: str
    source_uri: str
    title: Optional[str] = None


class DocumentLoader:
    """Loads documents from various sources (markdown files, folder, websites)."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def load(self, uri: str, document_type: str) -> List[LoadedDocument]:
        """
        Load a document from the given URI based on its type.
        
        Args:
            uri: The URI of the document (folder or unique file path or URL)
            document_type: Type of document ('markdown', 'folder' or 'website')
            
        Returns:
            LoadedDocument with content and metadata
        """
        if document_type == "markdown":
            return await self._load_markdown(uri)
        elif document_type == "website":
            return await self._load_website(uri)
        elif document_type == "folder":
            return self._load_directory(uri)
        else:
            raise ValueError(f"Unsupported document type: {document_type}")

    async def _load_markdown(self, uri: str) -> List[LoadedDocument]:
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
        frontmatter, content = self._parse_frontmatter(content)
        if frontmatter:
            title = frontmatter.get("title", "")
            if not title:
                title = self._extract_markdown_title(content)
            uri = frontmatter.get("source_url", "")
            document_id = frontmatter.get("document_id", title+"_1")
        else:
            title = self._extract_markdown_title(content)
            document_id=title+"_1"
   
        return [LoadedDocument(
            document_id=document_id,
            content=content,
            content_hash=self._compute_hash(content),
            source_uri=uri,
            title=title
        )]

    async def _load_website(self, uri: str) -> List[LoadedDocument]:
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

        return [LoadedDocument(
            document_id=title+"_1",
            content=content,
            content_hash=self._compute_hash(content),
            source_uri=uri,
            title=title
        )]

    def _load_directory(self, uri: str) -> list[LoadedDocument]:
        """Load a directory and process all markdown files within it."""
        if uri.startswith("file://"):
            # Local file
            file_path = uri.replace("file://", "")
            path = Path(file_path)
        else:
            path = Path(uri)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {uri}")
        all_documents = []
        for file in path.glob("*.md"):
            if file.name == "README.md":
                continue
            content = file.read_text(encoding="utf-8")
            frontmatter, content = self._parse_frontmatter(content)
            if frontmatter:
                title = frontmatter.get("title", "")
                source_uri = frontmatter.get("source_url", str(file))
                document_id = frontmatter.get("document_id", file.name)
                if not title:
                    title = self._extract_markdown_title(content)
            else:
                title = self._extract_markdown_title(content)
                document_id = file.name
                source_uri = str(file)
            all_documents.append(LoadedDocument(
                document_id=document_id,
                content=content,
                content_hash=self._compute_hash(content),
                source_uri=source_uri,
                title=title
            ))
        return all_documents


    def _extract_markdown_title(self, content: str) -> Optional[str]:
        """Extract the first H1 title from markdown content."""
        # Look for # Title pattern
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content.
        frontmatter is between the first and second --- boundaries
        returns the frontmatter and the content after the second --- boundary
        if there is no frontmatter, returns an empty dictionary and the content
        if there is an error parsing the frontmatter, returns an empty dictionary and the content
        if there is no content after the second --- boundary, returns an empty dictionary and the content
        """
        if not content.startswith("---\n"):
            return {}, content

        try:
            # Split on the second --- boundary
            parts = content.split("---\n", 2)
            if len(parts) < 3:
                return {}, content

            frontmatter = yaml.safe_load(parts[1])
            markdown_content = parts[2]
            return frontmatter or {}, markdown_content
        except yaml.YAMLError:
            return {}, content

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content for change detection."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

