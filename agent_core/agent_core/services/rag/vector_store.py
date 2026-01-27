"""Vector storage using ChromaDB for knowledge metadata and content."""

import logging
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from agent_core.services.rag.models import SearchResults
from agent_core.services.rag.text_splitter import TextChunk

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector storage using ChromaDB for knowledge content and metadata."""

    def __init__(
        self,
        chroma_path: str,
        embedding_model: str,
        max_results: int = 5,
        collection_name: str = "knowledge_base"
    ):
        self.max_results = max_results
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=chroma_path, settings=Settings(anonymized_telemetry=False)
        )

        # Set up sentence transformer embedding function
        self.embedding_function = (
            chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            )
        )

        # Create collections for different types of data
        self.knowledge_metadata = self._create_collection(
            f"{collection_name}_metadata"
        )  # Knowledge metadata (title, uri, category, tags)
        self.knowledge_content = self._create_collection(
            f"{collection_name}_content"
        )  # Actual knowledge content chunks

    def _create_collection(self, name: str):
        """Create or get a ChromaDB collection."""
        return self.client.get_or_create_collection(
            name=name, embedding_function=self.embedding_function
        )

    def search(
        self,
        query: str,
        knowledge_id: Optional[int] = None,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> SearchResults:
        """
        Main search interface that handles knowledge content search.

        Args:
            query: What to search for in knowledge content
            knowledge_id: Optional knowledge ID to filter by
            category: Optional category to filter by
            tags: Optional tags to filter by
            limit: Maximum results to return

        Returns:
            SearchResults object with documents and metadata
        """
        # Build filter for content search
        filter_dict = self._build_filter(knowledge_id, category, tags)

        # Use provided limit or fall back to configured max_results
        search_limit = limit if limit is not None else self.max_results

        try:
            results = self.knowledge_content.query(
                query_texts=[query], n_results=search_limit, where=filter_dict
            )
            return SearchResults.from_chroma(results)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return SearchResults.empty(f"Search error: {str(e)}")

    def _build_filter(
        self,
        knowledge_id: Optional[int],
        category: Optional[str],
        tags: Optional[str],
    ) -> Optional[Dict]:
        """Build ChromaDB filter from search parameters."""
        conditions = []
        
        if knowledge_id is not None:
            conditions.append({"knowledge_id": knowledge_id})
        
        if category:
            conditions.append({"category": category})
        
        if tags:
            conditions.append({"tags": tags})
        
        if not conditions:
            return None
        
        if len(conditions) == 1:
            return conditions[0]
        
        return {"$and": conditions}

    def add_knowledge_metadata(
        self,
        knowledge_id: int,
        title: str,
        uri: str,
        category: Optional[str] = None,
        tags: Optional[str] = None,
    ):
        """Add knowledge information to the metadata collection."""
        self.knowledge_metadata.add(
            documents=[title],
            metadatas=[
                {
                    "knowledge_id": knowledge_id,
                    "title": title,
                    "uri": uri,
                    "category": category or "",
                    "tags": tags or "",
                }
            ],
            ids=[str(knowledge_id)],
        )

    def add_knowledge_content(self, chunks: List[TextChunk]):
        """Add knowledge content chunks to the vector store."""
        if not chunks:
            return

        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "knowledge_id": chunk.metadata.get("knowledge_id"),
                "title": chunk.metadata.get("title", ""),
                "uri": chunk.metadata.get("uri", ""),
                "category": chunk.metadata.get("category", ""),
                "tags": chunk.metadata.get("tags", ""),
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ]
        # Use knowledge_id with chunk index for unique IDs
        ids = [
            f"{chunk.metadata.get('knowledge_id')}_{chunk.chunk_index}"
            for chunk in chunks
        ]

        self.knowledge_content.add(documents=documents, metadatas=metadatas, ids=ids)

    def remove_knowledge_metadata(self, knowledge_id: int) -> bool:
        """Remove knowledge metadata from the collection."""
        try:
            self.knowledge_metadata.delete(ids=[str(knowledge_id)])
            return True
        except Exception as e:
            logger.error(f"Error removing knowledge metadata {knowledge_id}: {e}")
            return True  # Return True even if not found

    def remove_knowledge_content(self, knowledge_id: int) -> bool:
        """Remove all chunks for a knowledge item from the vector store."""
        try:
            # Find all chunks for this knowledge item
            results = self.knowledge_content.get(
                where={"knowledge_id": knowledge_id}, include=[]
            )

            if results["ids"]:
                self.knowledge_content.delete(ids=results["ids"])
                logger.info(
                    f"Removed {len(results['ids'])} chunks for knowledge item {knowledge_id}"
                )

            return True
        except Exception as e:
            logger.error(f"Error removing knowledge content {knowledge_id}: {e}")
            return True  # Return True even if not found

    def get_knowledge_metadata(self, knowledge_id: int) -> Optional[Dict[str, Any]]:
        """Get metadata for a knowledge item."""
        try:
            results = self.knowledge_metadata.get(ids=[str(knowledge_id)])
            if results and results["metadatas"]:
                return results["metadatas"][0]
            return None
        except Exception as e:
            logger.error(f"Error getting knowledge metadata {knowledge_id}: {e}")
            return None

    def get_existing_knowledge_ids(self) -> List[str]:
        """Get all existing knowledge IDs from the vector store."""
        try:
            results = self.knowledge_metadata.get()
            if results and "ids" in results:
                return results["ids"]
            return []
        except Exception as e:
            logger.error(f"Error getting existing knowledge IDs: {e}")
            return []

    def get_knowledge_count(self) -> int:
        """Get the total number of knowledge items in the vector store."""
        try:
            return self.knowledge_metadata.count()
        except Exception as e:
            logger.error(f"Error getting knowledge count: {e}")
            return 0

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collections."""
        try:
            total_chunks = self.knowledge_content.count()
            
            # Get unique knowledge items
            if total_chunks > 0:
                all_metadata = self.knowledge_content.get(include=["metadatas"])
                if all_metadata and "metadatas" in all_metadata:
                    knowledge_ids = set(
                        m.get("knowledge_id") for m in all_metadata["metadatas"]
                    )
                    unique_knowledge_items = len(knowledge_ids)
                else:
                    unique_knowledge_items = 0
            else:
                unique_knowledge_items = 0

            return {
                "total_chunks": total_chunks,
                "unique_knowledge_items": unique_knowledge_items,
                "collection_name": f"{self.collection_name}_content",
                "embedding_model": "all-MiniLM-L6-v2",  # TODO: get from config
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                "total_chunks": 0,
                "unique_knowledge_items": 0,
                "collection_name": f"{self.collection_name}_content",
                "embedding_model": "all-MiniLM-L6-v2",
            }
