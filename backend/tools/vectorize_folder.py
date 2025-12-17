#!/usr/bin/env python3
"""
Tool to vectorize folder content into ChromaDB for RAG.

This script scans a folder for supported documents (markdown, text, HTML),
processes them through the RAG pipeline, stores embeddings in ChromaDB,
and saves metadata to the knowledge base database.

The tool is reentrant: re-running it will update existing documents if their
content has changed, and skip unchanged files.

Usage:
    python -m tools.vectorize_folder /path/to/folder
    python -m tools.vectorize_folder /path/to/folder --extensions .md .txt --chunk-size 500
"""

import argparse
import asyncio
import hashlib
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.models import Base, Knowledge
from app.db.crud import get_knowledge_by_uri, create_knowledge, update_knowledge
from app.api.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate
from app.rag.document_loader import DocumentLoader
from app.rag.text_splitter import RecursiveTextSplitter
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Suppress SQLAlchemy echo logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Default supported file extensions
DEFAULT_EXTENSIONS = {".md", ".markdown", ".txt"}

# Extension to document type mapping
EXTENSION_TYPE_MAP = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".html": "html",
    ".htm": "html",
}


class FolderVectorizer:
    """Vectorizes folder content into ChromaDB and saves to knowledge database."""

    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = "knowledge_base",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_model: str = "all-MiniLM-L6-v2",
        database_url: Optional[str] = None
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.database_url = database_url or get_settings().database_url
        
        # Ensure persist directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Use sentence-transformers for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize document loader and text splitter
        self.document_loader = DocumentLoader()
        self.text_splitter = RecursiveTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Database engine and session maker
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            future=True,
        )
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def init_db(self):
        """Initialize the database tables if they don't exist."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _get_document_type(self, file_path: Path) -> str:
        """Determine document type based on file extension."""
        ext = file_path.suffix.lower()
        return EXTENSION_TYPE_MAP.get(ext, "text")

    async def _load_text_file(self, file_path: Path) -> tuple[str, str]:
        """Load a plain text file."""
        content = file_path.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return content, content_hash

    async def _load_html_file(self, file_path: Path) -> tuple[str, str, Optional[str]]:
        """Load and convert an HTML file to text."""
        from bs4 import BeautifulSoup
        from markdownify import markdownify
        import re
        
        html_content = file_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        # Find main content
        main_content = (
            soup.find("main") or
            soup.find("article") or
            soup.find("div", class_=re.compile(r"content|main|article", re.I)) or
            soup.find("body")
        )
        
        if main_content:
            content = markdownify(str(main_content), heading_style="ATX", strip=["a"])
        else:
            content = soup.get_text(separator="\n", strip=True)
        
        content = re.sub(r"\n{3,}", "\n\n", content).strip()
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        # Extract title
        title = None
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        return content, content_hash, title

    async def _remove_chunks_for_knowledge(self, knowledge_id: int):
        """Remove all chunks for a knowledge item from ChromaDB."""
        try:
            results = self.collection.get(
                where={"knowledge_id": knowledge_id},
                include=[]
            )
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.debug(f"Removed {len(results['ids'])} existing chunks for knowledge_id={knowledge_id}")
        except Exception as e:
            logger.warning(f"Error removing chunks for knowledge_id={knowledge_id}: {e}")

    async def _index_to_chromadb(
        self,
        knowledge_id: int,
        title: str,
        uri: str,
        document_type: str,
        content: str,
        content_hash: str,
        category: Optional[str] = None,
        tags: Optional[str] = None
    ) -> int:
        """Index document content to ChromaDB. Returns number of chunks created."""
        # Create metadata
        metadata = {
            "knowledge_id": knowledge_id,
            "title": title,
            "uri": uri,
            "document_type": document_type,
            "category": category or "",
            "tags": tags or "",
            "indexed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Split into chunks
        chunks = self.text_splitter.split_text(content, metadata)
        
        if not chunks:
            return 0
        
        # Prepare data for ChromaDB (using kb_ prefix to match existing RAG service)
        ids = [f"kb_{knowledge_id}_chunk_{i}" for i in range(len(chunks))]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                **metadata,
                "chunk_index": chunk.chunk_index,
                "start_index": chunk.start_index
            }
            for chunk in chunks
        ]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        return len(chunks)

    async def vectorize_file(
        self,
        file_path: Path,
        base_folder: Path,
        db: AsyncSession,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        force: bool = False
    ) -> dict:
        """
        Vectorize a single file and save to database.
        
        Args:
            file_path: Path to the file
            base_folder: Base folder for relative path computation
            db: Database session
            category: Optional category
            tags: Optional tags
            force: Force re-indexing even if content unchanged
        
        Returns:
            Dict with status information
        """
        relative_path = str(file_path.relative_to(base_folder))
        doc_type = self._get_document_type(file_path)
        uri = f"file://{file_path.absolute()}"
        
        try:
            # Load document based on type
            title = None
            if doc_type == "markdown":
                loaded = await self.document_loader._load_markdown(str(file_path))
                content = loaded.content
                content_hash = loaded.content_hash
                title = loaded.title
            elif doc_type == "html":
                content, content_hash, title = await self._load_html_file(file_path)
            else:
                content, content_hash = await self._load_text_file(file_path)
            
            if not content.strip():
                return {
                    "file": relative_path,
                    "status": "skipped",
                    "reason": "empty content",
                    "chunks": 0,
                    "action": "none"
                }
            
            # Use filename as title if not extracted
            if not title:
                title = file_path.stem
            
            # Check if document already exists in database
            existing_knowledge = await get_knowledge_by_uri(db, uri)
            
            if existing_knowledge:
                # Document exists - check if content has changed
                if existing_knowledge.content_hash == content_hash and not force:
                    return {
                        "file": relative_path,
                        "status": "skipped",
                        "reason": "content unchanged",
                        "chunks": 0,
                        "action": "none",
                        "knowledge_id": existing_knowledge.id
                    }
                
                # Content changed - update database record
                knowledge_update = KnowledgeUpdate(
                    title=title,
                    content_hash=content_hash,
                    last_fetched_at=datetime.now(timezone.utc),
                    status="active"
                )
                # Update category/tags only if provided
                if category:
                    knowledge_update.category = category
                if tags:
                    knowledge_update.tags = tags
                
                await update_knowledge(db, existing_knowledge.id, knowledge_update)
                knowledge_id = existing_knowledge.id
                action = "updated"
                
                # Remove old chunks before re-indexing
                await self._remove_chunks_for_knowledge(knowledge_id)
                
            else:
                # New document - create database record
                knowledge_create = KnowledgeCreate(
                    title=title,
                    description=f"Imported from {relative_path}",
                    document_type=doc_type,
                    uri=uri,
                    category=category,
                    tags=tags,
                    status="active"
                )
                new_knowledge = await create_knowledge(db, knowledge_create)
                
                # Update with content_hash and last_fetched_at
                await update_knowledge(
                    db,
                    new_knowledge.id,
                    KnowledgeUpdate(
                        content_hash=content_hash,
                        last_fetched_at=datetime.now(timezone.utc)
                    )
                )
                knowledge_id = new_knowledge.id
                action = "created"
            
            # Index to ChromaDB
            num_chunks = await self._index_to_chromadb(
                knowledge_id=knowledge_id,
                title=title,
                uri=uri,
                document_type=doc_type,
                content=content,
                content_hash=content_hash,
                category=category,
                tags=tags
            )
            
            # Update indexed_at timestamp after successful indexing
            if num_chunks > 0:
                await update_knowledge(
                    db,
                    knowledge_id,
                    KnowledgeUpdate(indexed_at=datetime.now(timezone.utc))
                )
            
            return {
                "file": relative_path,
                "status": "success",
                "chunks": num_chunks,
                "title": title,
                "action": action,
                "knowledge_id": knowledge_id
            }
            
        except Exception as e:
            logger.error(f"Error processing {relative_path}: {e}")
            return {
                "file": relative_path,
                "status": "error",
                "error": str(e),
                "chunks": 0,
                "action": "none"
            }

    async def vectorize_folder(
        self,
        folder_path: Path,
        extensions: set[str],
        category: Optional[str] = None,
        tags: Optional[str] = None,
        recursive: bool = True,
        force: bool = False
    ) -> dict:
        """
        Vectorize all supported files in a folder.
        
        Args:
            folder_path: Path to the folder to process
            extensions: Set of file extensions to include (e.g., {".md", ".txt"})
            category: Optional category to assign to all documents
            tags: Optional comma-separated tags to assign to all documents
            recursive: Whether to process subdirectories
            force: Force re-indexing even if content unchanged
            
        Returns:
            Summary dict with processing results
        """
        folder_path = folder_path.resolve()
        
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        if not folder_path.is_dir():
            raise ValueError(f"Not a directory: {folder_path}")
        
        # Initialize database
        await self.init_db()
        
        # Find all matching files
        if recursive:
            files = [
                f for f in folder_path.rglob("*")
                if f.is_file() and f.suffix.lower() in extensions
            ]
        else:
            files = [
                f for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower() in extensions
            ]
        
        # Sort for consistent ordering
        files.sort()
        
        logger.info(f"Found {len(files)} files to process in {folder_path}")
        
        results = {
            "folder": str(folder_path),
            "total_files": len(files),
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "total_chunks": 0,
            "files": []
        }
        
        async with self.async_session_maker() as db:
            for i, file_path in enumerate(files, 1):
                logger.info(f"[{i}/{len(files)}] Processing: {file_path.relative_to(folder_path)}")
                
                result = await self.vectorize_file(
                    file_path,
                    folder_path,
                    db,
                    category=category,
                    tags=tags,
                    force=force
                )
                
                results["files"].append(result)
                
                if result["status"] == "success":
                    results["total_chunks"] += result["chunks"]
                    if result["action"] == "created":
                        results["created"] += 1
                    elif result["action"] == "updated":
                        results["updated"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["errors"] += 1
        
        return results

    def get_stats(self) -> dict:
        """Get current collection statistics."""
        count = self.collection.count()
        
        unique_docs = 0
        if count > 0:
            all_metadata = self.collection.get(include=["metadatas"])
            knowledge_ids = set(m.get("knowledge_id", 0) for m in all_metadata["metadatas"])
            unique_docs = len(knowledge_ids)
        
        return {
            "total_chunks": count,
            "unique_documents": unique_docs,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory
        }


async def main():
    parser = argparse.ArgumentParser(
        description="Vectorize folder content into ChromaDB for RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Vectorize markdown files in a folder
    python -m tools.vectorize_folder /path/to/docs

    # Vectorize with custom extensions and chunk size
    python -m tools.vectorize_folder /path/to/docs --extensions .md .txt .html --chunk-size 500

    # Vectorize with category and tags
    python -m tools.vectorize_folder /path/to/docs --category "Documentation" --tags "api,reference"

    # Force re-index all files (ignore content hash)
    python -m tools.vectorize_folder /path/to/docs --force

    # Non-recursive processing
    python -m tools.vectorize_folder /path/to/docs --no-recursive
        """
    )
    
    parser.add_argument(
        "folder",
        type=Path,
        help="Path to folder containing documents to vectorize"
    )
    
    parser.add_argument(
        "--extensions", "-e",
        nargs="+",
        default=list(DEFAULT_EXTENSIONS),
        help=f"File extensions to process (default: {' '.join(DEFAULT_EXTENSIONS)})"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Maximum chunk size in characters (default: 1000)"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Overlap between chunks in characters (default: 200)"
    )
    
    parser.add_argument(
        "--persist-dir",
        type=str,
        default="./data/chroma",
        help="ChromaDB persistence directory (default: ./data/chroma)"
    )
    
    parser.add_argument(
        "--collection",
        type=str,
        default="knowledge_base",
        help="ChromaDB collection name (default: knowledge_base)"
    )
    
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model for embeddings (default: all-MiniLM-L6-v2)"
    )
    
    parser.add_argument(
        "--category",
        type=str,
        help="Category to assign to all documents"
    )
    
    parser.add_argument(
        "--tags",
        type=str,
        help="Comma-separated tags to assign to all documents"
    )
    
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not process subdirectories"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-indexing even if content unchanged"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show collection statistics, do not process files"
    )
    
    parser.add_argument(
        "--database-url",
        type=str,
        help="Database URL (default: from settings)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Normalize extensions
    extensions = {ext if ext.startswith(".") else f".{ext}" for ext in args.extensions}
    
    logger.info("Initializing vectorizer...")
    vectorizer = FolderVectorizer(
        persist_directory=args.persist_dir,
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        embedding_model=args.embedding_model,
        database_url=args.database_url
    )
    
    if args.stats_only:
        stats = vectorizer.get_stats()
        print("\nCollection Statistics:")
        print(f"  Collection: {stats['collection_name']}")
        print(f"  Persist Directory: {stats['persist_directory']}")
        print(f"  Total Chunks: {stats['total_chunks']}")
        print(f"  Unique Documents: {stats['unique_documents']}")
        return
    
    logger.info(f"Processing folder: {args.folder}")
    logger.info(f"Extensions: {extensions}")
    logger.info(f"Chunk size: {args.chunk_size}, Overlap: {args.chunk_overlap}")
    if args.force:
        logger.info("Force mode: will re-index all files regardless of content changes")
    
    results = await vectorizer.vectorize_folder(
        args.folder,
        extensions=extensions,
        category=args.category,
        tags=args.tags,
        recursive=not args.no_recursive,
        force=args.force
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("VECTORIZATION COMPLETE")
    print("=" * 60)
    print(f"Folder: {results['folder']}")
    print(f"Total files found: {results['total_files']}")
    print(f"Created (new): {results['created']}")
    print(f"Updated (changed): {results['updated']}")
    print(f"Skipped (unchanged): {results['skipped']}")
    print(f"Errors: {results['errors']}")
    print(f"Total chunks created: {results['total_chunks']}")
    
    if args.verbose and results["files"]:
        print("\nFile Details:")
        for file_result in results["files"]:
            if file_result["status"] == "success":
                status_icon = "+" if file_result["action"] == "created" else "~"
            elif file_result["status"] == "error":
                status_icon = "!"
            else:
                status_icon = "-"
            
            print(f"  {status_icon} {file_result['file']}: {file_result['status']}", end="")
            if file_result.get("action") and file_result["action"] != "none":
                print(f" ({file_result['action']})", end="")
            if file_result.get("chunks"):
                print(f" - {file_result['chunks']} chunks")
            elif file_result.get("error"):
                print(f" - {file_result['error']}")
            elif file_result.get("reason"):
                print(f" - {file_result['reason']}")
            else:
                print()
    
    # Print final stats
    stats = vectorizer.get_stats()
    print(f"\nCollection now contains {stats['total_chunks']} chunks from {stats['unique_documents']} documents")


if __name__ == "__main__":
    asyncio.run(main())
