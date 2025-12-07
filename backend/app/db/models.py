from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Integer, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status: Open, Started, Completed, Cancelled
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Open")
    
    # Priority/Urgency: Urgent, Not Urgent
    urgency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Importance: Important, Not Important
    importance: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Category for grouping todos
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False, 
        server_default=func.now(), 
        onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Due date for the todo
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Source reference (e.g., meeting note ID, knowledge reference ID)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"Todo(id={self.id!r}, title={self.title!r}, status={self.status!r})"


class Knowledge(Base):
    __tablename__ = "knowledge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Document type: markdown, website
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # URI reference (file path or URL)
    uri: Mapped[str] = mapped_column(String(2048), nullable=False)
    
    # SHA256 hash of content for change detection (useful for RAG)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Status: active, pending, error, archived
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    
    # Timestamp when document was first referenced
    referenced_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )
    
    # Timestamp of last content fetch (for refresh tracking)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Standard timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False, 
        server_default=func.now(), 
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"Knowledge(id={self.id!r}, title={self.title!r}, document_type={self.document_type!r})"

