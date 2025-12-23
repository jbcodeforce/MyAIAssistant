from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stakeholders: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    team: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_products: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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

    # Relationships
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="organization")

    def __repr__(self) -> str:
        return f"Organization(id={self.id!r}, name={self.name!r})"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True
    )
    # Status: Draft, Active, On Hold, Completed, Cancelled
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    # Bullet list of small tasks stored as markdown text
    tasks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Past steps taken to address the project's challenges
    past_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="projects")
    todos: Mapped[list["Todo"]] = relationship("Todo", back_populates="project")

    def __repr__(self) -> str:
        return f"Project(id={self.id!r}, name={self.name!r}, status={self.status!r})"


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
    
    # Link to project (optional)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    
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

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="todos")

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
    
    # Category for classification
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Tags for flexible querying (stored as comma-separated values)
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
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
    
    # Timestamp when document was indexed into the RAG system
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
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
        return f"Knowledge(id={self.id!r}, title={self.title!r}, category={self.category!r})"


class TaskPlan(Base):
    __tablename__ = "task_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    todo_id: Mapped[int] = mapped_column(Integer, ForeignKey("todos.id", ondelete="CASCADE"), nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
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

    # Relationship to Todo
    todo: Mapped["Todo"] = relationship("Todo", backref="task_plan")

    def __repr__(self) -> str:
        return f"TaskPlan(id={self.id!r}, todo_id={self.todo_id!r})"


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # LLM Configuration
    llm_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    llm_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    llm_api_endpoint: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    default_temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.7)
    
    # RAG Configuration
    chunk_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1000)
    overlap: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=200)
    min_chunk_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=100)
    
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

    def __repr__(self) -> str:
        return f"Settings(id={self.id!r}, llm_name={self.llm_name!r})"
