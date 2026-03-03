"""Chat compatibility routes: same request/response shape as backend for proxy."""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent_service.agents.chat import get_chat_agent

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessageInput(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatTodoRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_history: list[ChatMessageInput] = Field(default=[])
    use_rag: bool = True
    task_title: str | None = None
    task_description: str | None = None
    context_used: list[dict] | None = None


class ContextItem(BaseModel):
    title: str = ""
    uri: str = ""
    score: float = 0.0
    snippet: str = ""


class ChatResponse(BaseModel):
    message: str = Field(..., description="Assistant response")
    context_used: list[ContextItem] = Field(default_factory=list)


class ChatGenericRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_history: list[ChatMessageInput] = Field(default=[])
    context: dict | None = None
    force_intent: str | None = None


class ChatGenericResponse(ChatResponse):
    intent: str | None = None
    agent_type: str | None = None
    confidence: float | None = None


def _format_message(req: ChatTodoRequest | ChatGenericRequest) -> str:
    """Build a single user message including conversation history and context."""
    parts = []
    if isinstance(req, ChatTodoRequest) and (req.task_title or req.task_description):
        parts.append("Task context:")
        if req.task_title:
            parts.append(f"Title: {req.task_title}")
        if req.task_description:
            parts.append(f"Description: {req.task_description}")
        parts.append("")
    if req.conversation_history:
        parts.append("Previous messages:")
        for m in req.conversation_history[-10:]:
            parts.append(f"{m.role}: {m.content}")
        parts.append("")
    if isinstance(req, ChatGenericRequest) and req.context:
        for k, v in req.context.items():
            if k in ("data_query_provider", "rag_category", "rag_top_k"):
                continue
            parts.append(f"{k}: {v}")
        if parts:
            parts.append("")
    parts.append(f"User: {req.message}")
    return "\n".join(parts)


@router.post("/todo", response_model=ChatResponse)
async def chat_todo(body: ChatTodoRequest):
    """Task-specific chat; backend proxies POST /api/chat/todo/{todo_id} after loading task."""
    try:
        agent = get_chat_agent()
        user_message = _format_message(body)
        run_output = await agent.arun(user_message)
        content = run_output.content if run_output else ""
        if isinstance(content, str):
            message = content
        else:
            message = str(content) if content is not None else ""
        context_used = []
        if run_output and getattr(run_output, "messages", None):
            for m in run_output.messages or []:
                if getattr(m, "content", None) and hasattr(m, "metadata") and m.metadata:
                    c = m.metadata.get("context_used") or m.metadata.get("citation")
                    if c:
                        context_used.extend(c if isinstance(c, list) else [c])
        return ChatResponse(
            message=message or "No response.",
            context_used=[ContextItem(
                title=(c.get("title") or "") if isinstance(c, dict) else "",
                uri=(c.get("uri") or "") if isinstance(c, dict) else "",
                score=float(c.get("score", 0)) if isinstance(c, dict) else 0.0,
                snippet=(c.get("snippet") or c.get("content") or "") if isinstance(c, dict) else str(c),
            ) for c in context_used[:20]],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {e!s}")


@router.post("/generic", response_model=ChatGenericResponse)
async def chat_generic(body: ChatGenericRequest):
    """Routed/generic chat; backend proxies POST /api/chat/generic."""
    try:
        agent = get_chat_agent()
        user_message = _format_message(body)
        run_output = await agent.arun(user_message)
        content = run_output.content if run_output else ""
        message = content if isinstance(content, str) else (str(content) if content else "")
        return ChatGenericResponse(
            message=message or "No response.",
            context_used=[],
            agent_type="Chat Agent",
            intent="general_chat",
            confidence=1.0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {e!s}")


@router.post("/generic/stream")
async def chat_generic_stream(body: ChatGenericRequest):
    """Stream generic chat as NDJSON. Backend proxies POST /api/chat/generic/stream."""
    async def generate():
        try:
            agent = get_chat_agent()
            user_message = _format_message(body)
            run_output = await agent.arun(user_message)
            content = run_output.content if run_output else ""
            message = content if isinstance(content, str) else (str(content) if content else "")
            chunk_size = 80
            for i in range(0, len(message), chunk_size):
                yield json.dumps({"content": message[i : i + chunk_size]}) + "\n"
            yield json.dumps({"done": True, "context_used": []}) + "\n"
        except Exception as e:
            yield json.dumps({"content": f"Error: {e}", "done": True}) + "\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
    )
