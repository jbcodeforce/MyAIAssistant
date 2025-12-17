"""API request/response schemas."""

from .chat import (
    ChatMessageInput,
    ChatRequest,
    RagChatRequest,
    ContextItem,
    ChatResponse,
    ChatConfigResponse,
)
from .customer import (
    CustomerBase,
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
)
from .knowledge import (
    KnowledgeBase,
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeResponse,
    KnowledgeListResponse,
)
from .project import (
    ProjectEntity,
    ProjectCreate,
    ProjectResponse,
    ProjectListResponse,
)
from .rag import (
    IndexKnowledgeRequest,
    IndexKnowledgeResponse,
    IndexAllResponse,
    SearchRequest,
    SearchResultItem,
    SearchResponse,
    RAGStatsResponse,
)
from .task_plan import (
    TaskPlanBase,
    TaskPlanCreate,
    TaskPlanUpdate,
    TaskPlanResponse,
)
from .todo import (
    TodoBase,
    TodoCreate,
    TodoUpdate,
    TodoResponse,
    TodoListResponse,
)

__all__ = [
    # Chat
    "ChatMessageInput",
    "ChatRequest",
    "RagChatRequest",
    "ContextItem",
    "ChatResponse",
    "ChatConfigResponse",
    # Customer
    "CustomerBase",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerListResponse",
    # Knowledge
    "KnowledgeBase",
    "KnowledgeCreate",
    "KnowledgeUpdate",
    "KnowledgeResponse",
    "KnowledgeListResponse",
    # Project
    "ProjectEntity",
    "ProjectCreate",
    "ProjectResponse",
    "ProjectListResponse",
    # RAG
    "IndexKnowledgeRequest",
    "IndexKnowledgeResponse",
    "IndexAllResponse",
    "SearchRequest",
    "SearchResultItem",
    "SearchResponse",
    "RAGStatsResponse",
    # Task Plan
    "TaskPlanBase",
    "TaskPlanCreate",
    "TaskPlanUpdate",
    "TaskPlanResponse",
    # Todo
    "TodoBase",
    "TodoCreate",
    "TodoUpdate",
    "TodoResponse",
    "TodoListResponse",
]

