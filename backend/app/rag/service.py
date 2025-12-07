"""RAG service for knowledge base indexing and retrieval."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from app.rag.document_loader import DocumentLoader
from app.rag.text_splitter import RecursiveTextSplitter

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A search result from the vector store."""
    content: str
    knowledge_id: int
    title: str
    uri: str
    score: float
    chunk_index: int


@dataclass
class IndexingResult:
    """Result of indexing a knowledge item."""
    success: bool
    chunks_indexed: int
    content_hash: str
    error: Optional[str] = None


class RAGService:
    """
    Service for RAG operations on the knowledge base.
    
    Handles document loading, chunking, embedding, and retrieval.
    """

    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = "knowledge_base",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Ensure persist directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Use sentence-transformers for embeddings (runs locally)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        # Get or create the collection
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
            document_type: Type of document ('markdown' or 'website')
            category: Optional category for filtering
            tags: Optional comma-separated tags
            
        Returns:
            IndexingResult with status and metadata
        """
        try:
            # First, remove any existing chunks for this knowledge item
            await self.remove_knowledge(knowledge_id)
            
            # Load the document
            logger.info(f"Loading document from {uri}")
            loaded_doc = await self.document_loader.load(uri, document_type)
            
            # Split into chunks
            metadata = {
                "knowledge_id": knowledge_id,
                "title": title,
                "uri": uri,
                "document_type": document_type,
                "category": category or "",
                "tags": tags or "",
                "indexed_at": datetime.now(timezone.utc).isoformat()
            }
            
            chunks = self.text_splitter.split_text(loaded_doc.content, metadata)
            
            if not chunks:
                return IndexingResult(
                    success=False,
                    chunks_indexed=0,
                    content_hash=loaded_doc.content_hash,
                    error="No content to index"
                )
            
            # Prepare data for ChromaDB
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
            
            logger.info(f"Indexed {len(chunks)} chunks for knowledge item {knowledge_id}")
            
            return IndexingResult(
                success=True,
                chunks_indexed=len(chunks),
                content_hash=loaded_doc.content_hash
            )
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return IndexingResult(
                success=False,
                chunks_indexed=0,
                content_hash="",
                error=f"File not found: {str(e)}"
            )
        except Exception as e:
            logger.exception(f"Error indexing knowledge item {knowledge_id}")
            return IndexingResult(
                success=False,
                chunks_indexed=0,
                content_hash="",
                error=str(e)
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
            # Find all chunks for this knowledge item
            results = self.collection.get(
                where={"knowledge_id": knowledge_id},
                include=[]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Removed {len(results['ids'])} chunks for knowledge item {knowledge_id}")
            
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
    ) -> list[SearchResult]:
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
        # Build where clause
        where = None
        where_conditions = []
        
        if category:
            where_conditions.append({"category": category})
        
        if knowledge_ids:
            where_conditions.append({"knowledge_id": {"$in": knowledge_ids}})
        
        if where_conditions:
            if len(where_conditions) == 1:
                where = where_conditions[0]
            else:
                where = {"$and": where_conditions}
        
        # Query the collection
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                
                # Convert distance to similarity score (cosine)
                # ChromaDB returns squared L2 distance for cosine, convert to similarity
                score = 1 - distance
                
                search_results.append(SearchResult(
                    content=results["documents"][0][i],
                    knowledge_id=metadata["knowledge_id"],
                    title=metadata["title"],
                    uri=metadata["uri"],
                    score=score,
                    chunk_index=metadata["chunk_index"]
                ))
        
        return search_results

    def get_collection_stats(self) -> dict:
        """Get statistics about the vector store collection."""
        count = self.collection.count()
        
        # Get unique knowledge items
        if count > 0:
            all_metadata = self.collection.get(include=["metadatas"])
            knowledge_ids = set(m["knowledge_id"] for m in all_metadata["metadatas"])
            unique_knowledge_items = len(knowledge_ids)
        else:
            unique_knowledge_items = 0
        
        return {
            "total_chunks": count,
            "unique_knowledge_items": unique_knowledge_items,
            "collection_name": self.collection_name,
            "embedding_model": "all-MiniLM-L6-v2"
        }


# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

