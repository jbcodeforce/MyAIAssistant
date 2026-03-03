"""Chat API endpoints for LLM-powered task planning."""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.db.database import get_db
from app.db import crud
from app.chat.service import ChatService, ChatMessage
from app.data_query.service import BackendDataQueryToolProvider
from app.core.config import get_settings
from app.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ContextItem
)
from app.services import agent_service_client

logger = logging.getLogger(__name__)

try:
    from agent_core.agents.query_classifier import QueryIntent
except ImportError:
    QueryIntent = None


def _normalize_context_used(context_used):
    """Ensure context_used is a list of dicts with title, uri, score, snippet/content."""
    if not isinstance(context_used, list):
        return []
    return [
        {
            "title": c.get("title", "") if isinstance(c, dict) else "",
            "uri": c.get("uri", "") if isinstance(c, dict) else "",
            "score": c.get("score") if isinstance(c, dict) else None,
            "snippet": (c.get("snippet") or c.get("content", "")) if isinstance(c, dict) else "",
            "content": c.get("content", "") if isinstance(c, dict) else "",
        }
        for c in context_used
        if isinstance(c, dict)
    ]



router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat(request: Request) -> ChatService:
    """Dependency to get the app-scoped chat service singleton (lazy init on first use)."""
    if request.app.state.chat_service is not None:
        return request.app.state.chat_service
    if getattr(request.app.state, "_chat_service_error", None) is not None:
        raise HTTPException(
            status_code=503,
            detail=f"Chat service unavailable: {request.app.state._chat_service_error}",
        )
    try:
        from app.chat.service import get_chat_service
        request.app.state.chat_service = get_chat_service()
        return request.app.state.chat_service
    except Exception as e:
        request.app.state._chat_service_error = str(e)
        raise HTTPException(
            status_code=503,
            detail=f"Chat service failed to initialize: {request.app.state._chat_service_error}",
        )


@router.post("/todo/{todo_id}", response_model=ChatResponse)
async def chat_about_todo(
    todo_id: int,
    request: ChatRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Chat with an AI assistant about a specific todo task.
    When AGENT_SERVICE_URL is set, the request is proxied to the agent-service.
    """
    todo = await crud.get_todo(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    history = [{"role": m.role, "content": m.content} for m in request.conversation_history]

    if get_settings().agent_service_url:
        try:
            data = await agent_service_client.chat_todo(
                message=request.message,
                conversation_history=history,
                task_title=todo.title,
                task_description=todo.description,
                use_rag=request.use_rag,
            )
            return ChatResponse(
                message=data.get("message", ""),
                context_used=[
                    ContextItem(
                        title=c.get("title", ""),
                        uri=c.get("uri", ""),
                        score=float(c.get("score", 0)),
                        snippet=c.get("snippet", ""),
                    )
                    for c in data.get("context_used", [])
                ],
            )
        except httpx.HTTPStatusError as e:
            logger.exception("Agent service chat/todo error")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            logger.exception("Agent service chat/todo error")
            raise HTTPException(status_code=503, detail=str(e))

    chat_service = get_chat(http_request)
    history_chat = [ChatMessage(role=msg.role, content=msg.content) for msg in request.conversation_history]
    try:
        response = await chat_service.chat_with_todo(
            todo_title=todo.title,
            todo_description=todo.description,
            user_message=request.message,
            conversation_history=history_chat,
            use_rag=request.use_rag,
        )
        normalized = _normalize_context_used(response.context_used)
        return ChatResponse(
            message=response.message,
            context_used=[
                ContextItem(
                    title=ctx["title"],
                    uri=ctx["uri"],
                    score=float(ctx["score"]) if ctx["score"] is not None else 0.0,
                    snippet=ctx["snippet"] or ctx["content"],
                )
                for ctx in normalized
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=f"Failed to get response from LLM: {str(e)}")


@router.post("/generic", response_model=ChatResponse)
async def generic_chat(request: ChatRequest, http_request: Request):
    """
    Generic chat with routing. When AGENT_SERVICE_URL is set, the request is proxied to the agent-service.
    """
    history = [{"role": m.role, "content": m.content} for m in request.conversation_history]
    context = dict(request.context or {})
    force_intent = request.force_intent

    if get_settings().agent_service_url:
        try:
            data = await agent_service_client.chat_generic(
                message=request.message,
                conversation_history=history,
                context=context,
                force_intent=force_intent,
            )
            return ChatResponse(
                message=data.get("message", ""),
                context_used=[
                    ContextItem(
                        title=c.get("title", ""),
                        uri=c.get("uri", ""),
                        score=float(c.get("score", 0)),
                        snippet=c.get("snippet", ""),
                    )
                    for c in data.get("context_used", [])
                ],
            )
        except httpx.HTTPStatusError as e:
            logger.exception("Agent service chat/generic error")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            logger.exception("Agent service chat/generic error")
            raise HTTPException(status_code=503, detail=str(e))

    chat_service = get_chat(http_request)
    history_chat = [ChatMessage(role=msg.role, content=msg.content) for msg in request.conversation_history]
    if force_intent and QueryIntent:
        try:
            force_intent = QueryIntent(force_intent)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid intent: {request.force_intent}")
    try:
        response = await chat_service.chat_with_routing(
            user_message=request.message,
            conversation_history=history_chat,
            context=context,
            force_intent=force_intent,
        )
        normalized = _normalize_context_used(response.context_used)
        return ChatResponse(
            message=response.message,
            context_used=[
                ContextItem(
                    title=ctx["title"],
                    uri=ctx["uri"],
                    score=float(ctx["score"]) if ctx["score"] is not None else 0.0,
                    snippet=ctx["snippet"] or ctx["content"],
                )
                for ctx in normalized
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("RAG chat error")
        raise HTTPException(status_code=500, detail=f"Failed to get response from LLM: {str(e)}")


@router.post("/generic/stream")
async def generic_chat_stream(
    request: ChatRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream generic chat as NDJSON. When AGENT_SERVICE_URL is set, the stream is proxied from the agent-service.
    """
    history = [{"role": m.role, "content": m.content} for m in request.conversation_history]
    context = dict(request.context or {})
    force_intent = request.force_intent

    if get_settings().agent_service_url:
        async def proxy_stream():
            try:
                async for line in agent_service_client.chat_generic_stream(
                    message=request.message,
                    conversation_history=history,
                    context=context,
                    force_intent=force_intent,
                ):
                    yield (line + "\n").encode("utf-8")
            except Exception as e:
                logger.exception("Agent service chat/generic/stream error")
                yield (json.dumps({"content": f"Error: {e}", "done": True}) + "\n").encode("utf-8")

        return StreamingResponse(proxy_stream(), media_type="application/x-ndjson")

    history_chat = [ChatMessage(role=msg.role, content=msg.content) for msg in request.conversation_history]
    force_intent_enum = None
    if request.force_intent and QueryIntent:
        try:
            force_intent_enum = QueryIntent(request.force_intent)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid intent: {request.force_intent}")
    context["data_query_provider"] = BackendDataQueryToolProvider(db=db)

    def _context_item_dict(ctx: dict) -> dict:
        return {
            "title": ctx.get("title", ""),
            "uri": ctx.get("uri", ""),
            "score": float(ctx["score"]) if ctx.get("score") is not None else 0.0,
            "snippet": ctx.get("snippet") or ctx.get("content", ""),
        }

    chat_service = get_chat(http_request)

    async def stream_generator():
        try:
            response = await chat_service.chat_with_routing(
                user_message=request.message,
                conversation_history=history_chat,
                context=context,
                force_intent=force_intent_enum,
            )
            normalized = _normalize_context_used(response.context_used)
            context_used = [_context_item_dict(ctx) for ctx in normalized]
            message = response.message or ""
            chunk_size = 80
            for i in range(0, len(message), chunk_size):
                yield (json.dumps({"content": message[i : i + chunk_size]}) + "\n").encode("utf-8")
            yield (json.dumps({"done": True, "context_used": context_used}) + "\n").encode("utf-8")
        except Exception as e:
            logger.exception("Generic chat stream error")
            yield (json.dumps({"content": f"Error: {e}", "done": True}) + "\n").encode("utf-8")

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")


@router.post("/kb", response_model=ChatResponse)
async def kb_chat(request: ChatRequest, http_request: Request):
    """
    Chat using the knowledge base. When AGENT_SERVICE_URL is set, proxied to agent-service as generic chat.
    """
    history = [{"role": m.role, "content": m.content} for m in request.conversation_history]
    if get_settings().agent_service_url:
        try:
            data = await agent_service_client.chat_generic(
                message=request.message,
                conversation_history=history,
                context={},
                force_intent=None,
            )
            return ChatResponse(
                message=data.get("message", ""),
                context_used=[
                    ContextItem(
                        title=c.get("title", ""),
                        uri=c.get("uri", ""),
                        score=float(c.get("score", 0)),
                        snippet=c.get("snippet", ""),
                    )
                    for c in data.get("context_used", [])
                ],
            )
        except httpx.HTTPStatusError as e:
            logger.exception("Agent service kb chat error")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            logger.exception("Agent service kb chat error")
            raise HTTPException(status_code=503, detail=str(e))

    chat_service = get_chat(http_request)
    history_chat = [ChatMessage(role=msg.role, content=msg.content) for msg in request.conversation_history]
    try:
        response = await chat_service.chat_with_kb(
            user_message=request.message,
            conversation_history=history_chat,
        )
        return ChatResponse(message=response.message, context_used=[])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("KB chat error")
        raise HTTPException(status_code=500, detail=f"Failed to get response from LLM: {str(e)}")


@router.get("/health")
async def chat_health_check():
    """
    Chat service health. When AGENT_SERVICE_URL is set, returns agent-service health; otherwise local LLM config.
    """
    if get_settings().agent_service_url:
        try:
            return await agent_service_client.health()
        except Exception as e:
            logger.exception("Agent service health check failed")
            raise HTTPException(status_code=503, detail=str(e))

    settings = get_settings()
    provider = settings.llm_provider
    has_api_key = settings.llm_api_key is not None
    if provider == "ollama":
        return {
            "status": "ready",
            "provider": provider,
            "model": settings.llm_model,
            "message": "Ollama is configured. Make sure Ollama is running locally.",
        }
    if has_api_key:
        return {
            "status": "ready",
            "provider": provider,
            "model": settings.llm_model,
            "message": f"{provider.capitalize()} API is configured.",
        }
    return {
        "status": "not_configured",
        "provider": provider,
        "model": settings.llm_model,
        "message": f"LLM_API_KEY environment variable is not set for {provider}.",
    }

