"""Meeting notes service for persisting meeting content to file system."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SavedNoteResult:
    """Result of saving a meeting note."""
    file_ref: str  # Relative path from notes_root
    absolute_path: Path  # Full path to the file


class MeetingNotesService:
    """
    Service for persisting meeting notes to the file system.
    
    Notes are saved under the configured notes_root directory with
    a structure based on organization, project, and meeting date.
    """

    def __init__(self, notes_root: str = None):
        settings = get_settings()
        self.notes_root = Path(notes_root or settings.notes_root)
        logger.debug(f"MeetingNotesService initialized with notes_root: {self.notes_root}")

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize a name for use in file paths.
        
        Converts to lowercase, replaces spaces with hyphens,
        and removes invalid characters.
        """
        # Convert to lowercase and replace spaces with hyphens
        sanitized = name.lower().replace(" ", "-")
        # Remove any characters that are not alphanumeric, hyphens, or underscores
        sanitized = re.sub(r"[^a-z0-9\-_]", "", sanitized)
        # Remove multiple consecutive hyphens
        sanitized = re.sub(r"-+", "-", sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip("-")
        return sanitized or "unknown"

    def _build_file_path(
        self,
        meeting_id: str,
        org_name: Optional[str] = None,
        project_name: Optional[str] = None,
        meeting_date: Optional[datetime] = None,
    ) -> str:
        """
        Build the relative file path for a meeting note.
        
        Structure: org_name/project_name/YYYY-MM-DD-meeting_id.md
        Falls back to 'general' for missing org/project.
        """
        date_str = (meeting_date or datetime.now()).strftime("%Y-%m-%d")
        
        # Build path components
        org_folder = self._sanitize_name(org_name) if org_name else "general"
        project_folder = self._sanitize_name(project_name) if project_name else "general"
        filename = f"{date_str}-{self._sanitize_name(meeting_id)}.md"
        
        return f"{org_folder}/{project_folder}/{filename}"

    async def save_note(
        self,
        meeting_id: str,
        content: str,
        org_name: Optional[str] = None,
        project_name: Optional[str] = None,
        meeting_date: Optional[datetime] = None,
    ) -> SavedNoteResult:
        """
        Save a meeting note to the file system.
        
        Args:
            meeting_id: Unique identifier for the meeting
            content: The markdown content of the meeting note
            org_name: Optional organization name for folder structure
            project_name: Optional project name for folder structure
            meeting_date: Optional date for the filename (defaults to today)
            
        Returns:
            SavedNoteResult with the file reference and absolute path
        """
        # Build the relative file path
        file_ref = self._build_file_path(
            meeting_id=meeting_id,
            org_name=org_name,
            project_name=project_name,
            meeting_date=meeting_date,
        )
        
        # Build absolute path
        absolute_path = self.notes_root / file_ref
        
        # Ensure parent directories exist
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content
        absolute_path.write_text(content, encoding="utf-8")
        logger.info(f"Saved meeting note to: {absolute_path}")
        
        return SavedNoteResult(
            file_ref=file_ref,
            absolute_path=absolute_path,
        )

    async def update_note(
        self,
        file_ref: str,
        content: str,
    ) -> SavedNoteResult:
        """
        Update an existing meeting note.
        
        Args:
            file_ref: The relative path to the file
            content: The new markdown content
            
        Returns:
            SavedNoteResult with the file reference and absolute path
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        absolute_path = self.notes_root / file_ref
        
        if not absolute_path.exists():
            raise FileNotFoundError(f"Meeting note not found: {file_ref}")
        
        absolute_path.write_text(content, encoding="utf-8")
        logger.info(f"Updated meeting note: {absolute_path}")
        
        return SavedNoteResult(
            file_ref=file_ref,
            absolute_path=absolute_path,
        )

    async def read_note(self, file_ref: str) -> str:
        """
        Read a meeting note from the file system.
        
        Args:
            file_ref: The relative path to the file
            
        Returns:
            The content of the meeting note
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        absolute_path = self.notes_root / file_ref
        
        if not absolute_path.exists():
            raise FileNotFoundError(f"Meeting note not found: {file_ref}")
        
        return absolute_path.read_text(encoding="utf-8")

    async def delete_note(self, file_ref: str) -> bool:
        """
        Delete a meeting note from the file system.
        
        Args:
            file_ref: The relative path to the file
            
        Returns:
            True if deleted, False if file didn't exist
        """
        absolute_path = self.notes_root / file_ref
        
        if not absolute_path.exists():
            return False
        
        absolute_path.unlink()
        logger.info(f"Deleted meeting note: {absolute_path}")
        
        # Try to clean up empty parent directories
        try:
            parent = absolute_path.parent
            while parent != self.notes_root and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        except OSError:
            pass  # Directory not empty or other error, ignore
        
        return True


# Global service instance
_meeting_notes_service: Optional[MeetingNotesService] = None


def get_meeting_notes_service() -> MeetingNotesService:
    """Get or create the global meeting notes service instance."""
    global _meeting_notes_service
    if _meeting_notes_service is None:
        _meeting_notes_service = MeetingNotesService()
    return _meeting_notes_service

