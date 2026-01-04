"""Text splitting utilities for chunking documents."""

from typing import Optional

from pydantic import BaseModel


class TextChunk(BaseModel):
    """A chunk of text with its metadata."""
    content: str
    start_index: int
    chunk_index: int
    metadata: dict


class RecursiveTextSplitter:
    """
    Splits text recursively using multiple separators.
    Inspired by LangChain's RecursiveCharacterTextSplitter.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[list[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str, metadata: Optional[dict] = None) -> list[TextChunk]:
        """
        Split text into chunks.
        
        Args:
            text: The text to split
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of TextChunk objects
        """
        chunks = self._split_text_recursive(text, self.separators)
        
        # Merge small chunks and create TextChunk objects
        result = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for chunk in chunks:
            if len(current_chunk) + len(chunk) <= self.chunk_size:
                if current_chunk:
                    current_chunk += " " + chunk
                else:
                    current_chunk = chunk
            else:
                if current_chunk:
                    result.append(TextChunk(
                        content=current_chunk.strip(),
                        start_index=current_start,
                        chunk_index=chunk_index,
                        metadata=metadata or {}
                    ))
                    chunk_index += 1
                    # Calculate overlap start
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                    current_start = current_start + len(current_chunk) - len(overlap_text)
                    current_chunk = overlap_text + " " + chunk if overlap_text else chunk
                else:
                    current_chunk = chunk

        # Add the last chunk
        if current_chunk.strip():
            result.append(TextChunk(
                content=current_chunk.strip(),
                start_index=current_start,
                chunk_index=chunk_index,
                metadata=metadata or {}
            ))

        return result

    def _split_text_recursive(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using the list of separators."""
        if not text:
            return []

        # Find the best separator to use
        separator = separators[-1]  # Default to last (empty string)
        for sep in separators:
            if sep in text:
                separator = sep
                break

        # Split the text
        if separator:
            splits = text.split(separator)
        else:
            # Character-level split
            splits = list(text)

        # Process splits
        chunks = []
        current = ""
        
        for split in splits:
            if not split:
                continue
                
            test_chunk = current + separator + split if current else split
            
            if len(test_chunk) <= self.chunk_size:
                current = test_chunk
            else:
                if current:
                    chunks.append(current)
                
                # If the split itself is too large, recursively split it
                if len(split) > self.chunk_size and separators[:-1]:
                    sub_chunks = self._split_text_recursive(split, separators[1:])
                    chunks.extend(sub_chunks)
                else:
                    current = split

        if current:
            chunks.append(current)

        return chunks

