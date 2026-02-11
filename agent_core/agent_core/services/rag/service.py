"""RAG service for knowledge base indexing and retrieval.

This module provides the RAGService class which orchestrates document processing,
vector storage, and retrieval operations using modular components.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List

from agent_core.services.rag.document_loader import DocumentLoader
from agent_core.services.rag.document_processor import DocumentProcessor
from agent_core.services.rag.models import (
    IndexingResult,
    SearchResult,
)
from agent_core.services.rag.text_splitter import TextChunk
from agent_core.services.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "knowledge_base")
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
OVERLAP: int = int(os.getenv("OVERLAP", "200"))
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


class RAGService:
    """
    Service for RAG operations on the knowledge base.
    
    Orchestrates document processing, vector storage, and retrieval operations
    using modular components (DocumentProcessor, VectorStore, DocumentLoader).
    
    Handles document loading, chunking, embedding, and retrieval.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        embedding_model: Optional[str] = None
    ):
        """
        Initialize RAGService with optional parameters.
        
        If parameters are not provided, uses environment variables or defaults.
        
        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name for the ChromaDB collections
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            embedding_model: Model name for embeddings
        """
        # Use provided values or fall back to environment variables or defaults
        self.persist_directory = persist_directory or CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or CHROMA_COLLECTION_NAME
        self.chunk_size = chunk_size if chunk_size is not None else CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else OVERLAP
        self.embedding_model = embedding_model or EMBEDDING_MODEL

        # Ensure persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize core components
        self.document_processor = DocumentProcessor(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )
        self.vector_store = VectorStore(
            chroma_path=self.persist_directory,
            embedding_model=self.embedding_model,
            max_results=5,
            collection_name=self.collection_name,
        )
        self.document_loader = DocumentLoader()

    async def index_knowledge(
        self,
        knowledge_id: int,
        title: str,
        uri: str,
        document_type: str,
        category: Optional[str] = None,
        tags: Optional[str] = None
    ) -> IndexingResult:
        """
        Index a knowledge item into the vector store.
        
        Args:
            knowledge_id: Database ID of the knowledge item
            title: Title of the knowledge item
            uri: URI to the document
            document_type: Type of document ('markdown', 'folder', or 'website')
            category: Optional category for filtering
            tags: Optional comma-separated tags
            
        Returns:
            IndexingResult with status and metadata
        """
        try:
            # First, remove any existing chunks for this knowledge item
            await self.remove_knowledge(knowledge_id)

            # Load the document (recursive for folder type so subfolders are included)
            logger.info(f"Loading document from {uri}")
            recursive = document_type == "folder"
            loaded_docs = await self.document_loader.load(
                uri, document_type, recursive=recursive
            )

            if not loaded_docs:
                return IndexingResult(
                    success=False,
                    chunks_indexed=0,
                    content_hash="",
                    error="No documents loaded",
                )

            total_chunks = 0
            content_hash = None

            for loaded_doc in loaded_docs:
                # Process the document
                metadata = {
                    "knowledge_id": knowledge_id,
                    "title": title or loaded_doc.title,
                    "uri": uri,
                    "document_type": document_type,
                    "category": category or "",
                    "tags": tags or "",
                }

                knowledge_item, chunks = self.document_processor.process_document(
                    loaded_doc=loaded_doc,
                    knowledge_id=knowledge_id,
                    title=title or loaded_doc.title,
                    metadata=metadata,
                )

                if not chunks:
                    continue

                # Add knowledge metadata (only once, use first doc's title if title not provided)
                if total_chunks == 0:
                    self.vector_store.add_knowledge_metadata(
                        knowledge_id=knowledge_id,
                        title=knowledge_item.title,
                        uri=knowledge_item.uri,
                        category=knowledge_item.category or "",
                        tags=knowledge_item.tags or "",
                    )

                # Convert KnowledgeChunk to TextChunk for vector store
                text_chunks = []
                for chunk in chunks:
                    text_chunk = TextChunk(
                        content=chunk.content,
                        start_index=0,  # Not used in vector store
                        chunk_index=chunk.chunk_index,
                        metadata=chunk.metadata,
                    )
                    text_chunks.append(text_chunk)

                # Add chunks to vector store
                self.vector_store.add_knowledge_content(text_chunks)
                total_chunks += len(chunks)
                content_hash = loaded_doc.content_hash

            if total_chunks == 0:
                return IndexingResult(
                    success=False,
                    chunks_indexed=0,
                    content_hash=content_hash or "",
                    error="No content to index",
                )

            logger.info(
                f"Indexed {total_chunks} chunks for knowledge item {knowledge_id}"
            )

            return IndexingResult(
                success=True, chunks_indexed=total_chunks, content_hash=content_hash or ""
            )

        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return IndexingResult(
                success=False,
                chunks_indexed=0,
                content_hash="",
                error=f"File not found: {str(e)}",
            )
        except Exception as e:
            logger.exception(f"Error indexing knowledge item {knowledge_id}")
            return IndexingResult(
                success=False,
                chunks_indexed=0,
                content_hash="",
                error=str(e),
            )

    async def remove_knowledge(self, knowledge_id: int) -> bool:
        """
        Remove all chunks for a knowledge item from the vector store.
        
        Args:
            knowledge_id: Database ID of the knowledge item
            
        Returns:
            True if successful
        """
        try:
            self.vector_store.remove_knowledge_content(knowledge_id)
            self.vector_store.remove_knowledge_metadata(knowledge_id)
            logger.info(f"Removed knowledge item {knowledge_id}")
            return True
        except Exception as e:
            logger.exception(f"Error removing knowledge item {knowledge_id}")
            return False

    async def search(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        knowledge_ids: Optional[list[int]] = None
    ) -> List[SearchResult]:
        """
        Search the knowledge base for relevant content.
        
        Args:
            query: The search query
            n_results: Maximum number of results to return
            category: Optional category filter
            tags: Optional list of tags to filter by
            knowledge_ids: Optional list of knowledge IDs to search within
            
        Returns:
            List of SearchResult objects ordered by relevance
        """
        # Build search parameters
        knowledge_id = None
        if knowledge_ids and len(knowledge_ids) == 1:
            knowledge_id = knowledge_ids[0]
        elif knowledge_ids and len(knowledge_ids) > 1:
            # VectorStore doesn't support multiple knowledge_ids yet
            # For now, search without filter and filter results
            knowledge_id = None

        # Convert tags list to string if provided
        tags_str = None
        if tags:
            tags_str = ",".join(tags)

        # Search using vector store
        search_results = self.vector_store.search(
            query=query,
            knowledge_id=knowledge_id,
            category=category,
            tags=tags_str,
            limit=n_results,
        )

        # Convert SearchResults to SearchResult list
        results = []
        if not search_results.is_empty():
            for i, doc in enumerate(search_results.documents):
                metadata = search_results.metadata[i]
                distance = search_results.distances[i]

                # Convert distance to similarity score (cosine)
                score = 1 - distance

                # Filter by knowledge_ids if multiple provided
                if knowledge_ids and len(knowledge_ids) > 1:
                    if metadata.get("knowledge_id") not in knowledge_ids:
                        continue

                result = SearchResult(
                    content=doc,
                    knowledge_id=metadata.get("knowledge_id"),
                    title=metadata.get("title", "Unknown"),
                    uri=metadata.get("uri", ""),
                    score=score,
                    chunk_index=metadata.get("chunk_index", 0),
                )
                results.append(result)

        return results

    def get_collection_stats(self) -> dict:
        """Get statistics about the vector store collection."""
        return self.vector_store.get_collection_stats()


    def process_directory(self,
        docs_dir: str = None,
        chunk_size: int = 5000,
        overlap: int = 200,
        min_chunk_size: int = 1000  ,
    ) -> List[str]:
        """
        Process all markdown files in the given directory.

        Args:
            docs_dir: Directory containing markdown files
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            min_chunk_size: Minimum size of each chunk

        Returns:
            List of all chunk documents
        """
        if docs_dir is None:
            docs_dir = Path(__file__).parent
        else:
            docs_dir = Path(docs_dir)

        all_chunks = []
        processed_count = 0

        # Process all .md files except README.md
        for md_file in docs_dir.glob("*.md"):
            if md_file.name == "README.md":
                continue

            print(f"Processing: {md_file.name}")
            chunks = self._process_document(md_file, chunk_size, overlap, min_chunk_size)
            all_chunks.extend(chunks)
            processed_count += 1

            if chunks:
                print(f"  → Generated {len(chunks)} chunks")

        logger.info(
            f"\nTotal: Processed {processed_count} documents, generated {len(all_chunks)} chunks"
        )
        return all_chunks


# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the global RAG service instance."""
    
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            collection_name=CHROMA_COLLECTION_NAME,
        )
    return _rag_service

