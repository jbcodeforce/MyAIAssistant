"""Knowledge processing service for batch document ingestion."""

import json
import os
import traceback
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, field_validator

from ai_assist_cli.services.api_client import (
    BackendClient,
    KnowledgeResponse,
    IndexKnowledgeResponse,
)


class KnowledgeDocumentSpec(BaseModel):
    """Specification for a knowledge document to be processed."""
    document_type: str
    uri: str
    collection: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        """Validate document type is one of the allowed values."""
        allowed = {"website", "folder", "markdown"}
        if v not in allowed:
            raise ValueError(f"document_type must be one of {allowed}, got '{v}'")
        return v

    @field_validator("uri")
    @classmethod
    def expand_uri(cls, v: str) -> str:
        """Expand environment variables and user home in URI."""
        # Expand ~ and $HOME style variables
        expanded = os.path.expanduser(v)
        expanded = os.path.expandvars(expanded)
        return expanded


class ProcessingAction(str):
    """Action taken during processing."""
    CREATED = "created"
    UPDATED = "updated"
    SKIPPED = "skipped"
    FAILED = "failed"


class ProcessingResult(BaseModel):
    """Result of processing a single document specification."""
    spec: KnowledgeDocumentSpec
    knowledge: Optional[KnowledgeResponse] = None
    indexing: Optional[IndexKnowledgeResponse] = None
    success: bool = False
    error: Optional[str] = None
    error_detail: Optional[str] = None  # traceback or response body for verbose
    action: str = ProcessingAction.FAILED  # created, updated, skipped, failed


class ProcessingSummary(BaseModel):
    """Summary of batch processing results."""
    total: int
    successful: int
    failed: int
    skipped: int = 0
    created: int = 0
    updated: int = 0
    results: list[ProcessingResult]


class KnowledgeProcessor:
    """Processes knowledge document specifications and indexes them via the backend API."""

    def __init__(self, backend_url: Optional[str] = None):
        """Initialize the processor.
        
        Args:
            backend_url: Optional backend API URL override
        """
        self.client = BackendClient(base_url=backend_url)

    @staticmethod
    def load_specs(json_path: Path) -> list[KnowledgeDocumentSpec]:
        """Load document specifications from a JSON file.
        
        Args:
            json_path: Path to the JSON file
            
        Returns:
            List of KnowledgeDocumentSpec objects
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the JSON is invalid
            pydantic.ValidationError: If the schema is invalid
        """
        if not json_path.exists():
            raise FileNotFoundError(f"File not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON file must contain a list of document specifications")

        return [KnowledgeDocumentSpec(**item) for item in data]

    @staticmethod
    def generate_title(spec: KnowledgeDocumentSpec) -> str:
        """Generate a title from the document specification if not provided.
        
        Args:
            spec: The document specification
            
        Returns:
            A generated or existing title
        """
        if spec.title:
            return spec.title

        if spec.document_type == "website":
            # Extract meaningful title from URL
            parsed = urlparse(spec.uri)
            path_parts = [p for p in parsed.path.split("/") if p]
            if path_parts:
                # Use last path segment, cleaned up
                title = path_parts[-1].replace("-", " ").replace("_", " ").title()
            else:
                title = parsed.netloc
            return title

        if spec.document_type in ("folder", "markdown"):
            # Use the folder/file name
            path = Path(spec.uri)
            return path.stem.replace("-", " ").replace("_", " ").title()

        return f"Document: {spec.uri[:50]}"

    async def process_spec(
        self,
        spec: KnowledgeDocumentSpec,
        force: bool = False
    ) -> ProcessingResult:
        """Process a single document specification.
        
        Args:
            spec: The document specification to process
            force: Force re-indexing even if content unchanged
            
        Returns:
            ProcessingResult with success/failure details
        """
        result = ProcessingResult(spec=spec)

        try:
            # Generate title if not provided
            title = self.generate_title(spec)

            # Check if knowledge item already exists
            existing = await self.client.get_knowledge_by_uri(spec.uri)
            
            if existing and not force:
                # Document exists - check if we should skip
                # The backend will compare content hashes during indexing
                # For now, we'll re-index to get updated content hash
                # but mark it as an update rather than create
                result.knowledge = existing
                result.action = ProcessingAction.UPDATED
                
                # Trigger re-indexing
                indexing = await self.client.index_knowledge(existing.id)
                result.indexing = indexing
                result.success = indexing.success
                
                # If content hash matches (no changes), mark as skipped
                if indexing.success and existing.content_hash and indexing.content_hash:
                    if existing.content_hash == indexing.content_hash:
                        result.action = ProcessingAction.SKIPPED
                
                if not indexing.success:
                    result.error = indexing.error
                    result.action = ProcessingAction.FAILED
            else:
                # Create new knowledge item or force re-index existing
                if existing and force:
                    # Use existing item but force re-index
                    result.knowledge = existing
                    result.action = ProcessingAction.UPDATED
                else:
                    # Create new knowledge item via API
                    knowledge = await self.client.create_knowledge(
                        title=title,
                        uri=spec.uri,
                        document_type=spec.document_type,
                        category=spec.collection,  # Map collection to category
                        description=spec.description,
                        tags=spec.tags,
                    )
                    result.knowledge = knowledge
                    result.action = ProcessingAction.CREATED

                # Trigger indexing
                indexing = await self.client.index_knowledge(result.knowledge.id)
                result.indexing = indexing
                result.success = indexing.success

                if not indexing.success:
                    result.error = indexing.error or "Indexing failed"
                    result.action = ProcessingAction.FAILED

        except httpx.HTTPStatusError as e:
            result.success = False
            result.action = ProcessingAction.FAILED
            body = (e.response.text or "").strip()
            if body and len(body) > 400:
                body = body[:400] + "..."
            result.error = f"HTTP {e.response.status_code}: {e.response.reason_phrase or 'Error'}"
            if body:
                result.error_detail = body
            else:
                result.error_detail = str(e)
        except httpx.RequestError as e:
            result.success = False
            result.action = ProcessingAction.FAILED
            result.error = f"Connection error: {type(e).__name__}"
            result.error_detail = str(e)
        except Exception as e:
            result.error = str(e)
            result.error_detail = traceback.format_exc()
            result.success = False
            result.action = ProcessingAction.FAILED

        return result

    async def process_all(
        self,
        specs: list[KnowledgeDocumentSpec],
        on_progress: Optional[callable] = None,
        force: bool = False,
    ) -> ProcessingSummary:
        """Process all document specifications.
        
        Args:
            specs: List of document specifications to process
            on_progress: Optional callback called after each item with (index, total, result)
            force: Force re-indexing even if content unchanged
            
        Returns:
            ProcessingSummary with all results
        """
        results: list[ProcessingResult] = []
        successful = 0
        failed = 0
        skipped = 0
        created = 0
        updated = 0

        for i, spec in enumerate(specs):
            result = await self.process_spec(spec, force=force)
            results.append(result)

            if result.success:
                successful += 1
                if result.action == ProcessingAction.CREATED:
                    created += 1
                elif result.action == ProcessingAction.UPDATED:
                    updated += 1
                elif result.action == ProcessingAction.SKIPPED:
                    skipped += 1
            else:
                failed += 1

            if on_progress:
                on_progress(i + 1, len(specs), result)

        return ProcessingSummary(
            total=len(specs),
            successful=successful,
            failed=failed,
            skipped=skipped,
            created=created,
            updated=updated,
            results=results,
        )

    async def get_stats(self) -> dict:
        """Get RAG vector store statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        return await self.client.get_rag_stats()

