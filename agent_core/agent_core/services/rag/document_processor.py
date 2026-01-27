"""Document processor for knowledge base documents."""

import logging
from typing import Dict, List, Optional

from agent_core.services.rag.document_loader import DocumentLoader, LoadedDocument
from agent_core.services.rag.models import KnowledgeItem, KnowledgeChunk
from agent_core.services.rag.text_splitter import RecursiveTextSplitter, TextChunk

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes knowledge base documents and extracts structured information."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def chunk_text(
        self, text: str, metadata: Optional[Dict] = None
    ) -> List[KnowledgeChunk]:
        """
        Split text into chunks and convert to KnowledgeChunk objects.

        Args:
            text: The text to split
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of KnowledgeChunk objects
        """
        if not text:
            return []

        # Use existing text splitter
        text_chunks = self.text_splitter.split_text(text, metadata)

        # Convert TextChunk to KnowledgeChunk
        knowledge_chunks = []
        for text_chunk in text_chunks:
            knowledge_chunk = KnowledgeChunk(
                content=text_chunk.content,
                knowledge_id=text_chunk.metadata.get("knowledge_id"),
                chunk_index=text_chunk.chunk_index,
                metadata=text_chunk.metadata.copy(),
            )
            knowledge_chunks.append(knowledge_chunk)

        return knowledge_chunks

    def process_document(
        self,
        loaded_doc: LoadedDocument,
        knowledge_id: int,
        title: str,
        metadata: Dict,
    ) -> tuple[KnowledgeItem, List[KnowledgeChunk]]:
        """
        Process a loaded document into a KnowledgeItem and chunks.

        Args:
            loaded_doc: LoadedDocument from DocumentLoader
            knowledge_id: ID of the knowledge item
            title: Title of the knowledge item
            metadata: Additional metadata (uri, document_type, category, tags, etc.)

        Returns:
            Tuple of (KnowledgeItem, List[KnowledgeChunk])
        """
        # Create KnowledgeItem
        knowledge_item = KnowledgeItem(
            knowledge_id=knowledge_id,
            title=title or loaded_doc.title or "Untitled",
            uri=metadata.get("uri", loaded_doc.source_uri),
            category=metadata.get("category"),
            tags=metadata.get("tags"),
        )

        # Prepare chunk metadata
        chunk_metadata = {
            "knowledge_id": knowledge_id,
            "title": knowledge_item.title,
            "uri": knowledge_item.uri,
            "category": metadata.get("category", ""),
            "tags": metadata.get("tags", ""),
            "document_type": metadata.get("document_type", ""),
            "content_hash": loaded_doc.content_hash,
        }

        # Chunk the content
        chunks = self.chunk_text(loaded_doc.content, chunk_metadata)

        return knowledge_item, chunks
