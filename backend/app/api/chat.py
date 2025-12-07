"""Chat API endpoints for LLM-powered task planning."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.chat.service import ChatService, ChatMessage, get_chat_service
from app.core.config import settings
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ContextItem,
    ChatConfigResponse,
    RagChatRequest,
)


router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat() -> ChatService:
    """Dependency to get the chat service."""
    return get_chat_service()


@router.post("/todo/{todo_id}", response_model=ChatResponse)
async def chat_about_todo(
    todo_id: int,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    chat: ChatService = Depends(get_chat)
):
    """
    Chat with an AI assistant about a specific todo task.
    
    The assistant can help plan how to approach and complete the task,
    using the knowledge base for relevant context.
    """
    # Get the todo item
    todo = await crud.get_todo(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # Convert conversation history
    history = [
        ChatMessage(role=msg.role, content=msg.content)
        for msg in request.conversation_history
    ]
    
    try:
        # Call the chat service
        response = await chat.chat_with_todo(
            todo_title=todo.title,
            todo_description=todo.description,
            user_message=request.message,
            conversation_history=history,
            use_rag=request.use_rag,
            rag_query=request.rag_query
        )
        
        return ChatResponse(
            message=response.message,
            context_used=[
                ContextItem(
                    title=ctx["title"],
                    uri=ctx["uri"],
                    score=ctx["score"],
                    snippet=ctx["snippet"]
                )
                for ctx in response.context_used
            ],
            model=response.model,
            provider=response.provider
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the error and return a user-friendly message
        import logging
        logging.exception("Chat error")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get response from LLM: {str(e)}"
        )


@router.post("/rag", response_model=ChatResponse)
async def chat_with_rag(
    request: RagChatRequest,
    chat: ChatService = Depends(get_chat)
):
    """
    Chat using the RAG knowledge base for context.
    
    This endpoint allows querying the knowledge base without 
    being tied to a specific todo task. Useful for general 
    questions about indexed documents.
    """
    # Convert conversation history
    history = [
        ChatMessage(role=msg.role, content=msg.content)
        for msg in request.conversation_history
    ]
    
    try:
        response = await chat.chat_with_rag(
            user_message=request.message,
            conversation_history=history,
            n_results=request.n_results
        )
        
        return ChatResponse(
            message=response.message,
            context_used=[
                ContextItem(
                    title=ctx["title"],
                    uri=ctx["uri"],
                    score=ctx["score"],
                    snippet=ctx["snippet"]
                )
                for ctx in response.context_used
            ],
            model=response.model,
            provider=response.provider
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        logging.exception("RAG chat error")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get response from LLM: {str(e)}"
        )


@router.get("/config", response_model=ChatConfigResponse)
async def get_chat_config():
    """
    Get the current chat configuration.
    
    Returns information about the LLM provider and settings.
    """
    return ChatConfigResponse(
        provider=settings.llm_provider,
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        rag_enabled=True
    )


@router.get("/health")
async def chat_health_check(chat: ChatService = Depends(get_chat)):
    """
    Check if the chat service is configured and ready.
    
    Returns the provider configuration status.
    """
    provider = settings.llm_provider
    has_api_key = settings.llm_api_key is not None
    
    if provider == "ollama":
        # Ollama doesn't need an API key
        return {
            "status": "ready",
            "provider": provider,
            "model": settings.llm_model,
            "message": "Ollama is configured. Make sure Ollama is running locally."
        }
    elif has_api_key:
        return {
            "status": "ready",
            "provider": provider,
            "model": settings.llm_model,
            "message": f"{provider.capitalize()} API is configured."
        }
    else:
        return {
            "status": "not_configured",
            "provider": provider,
            "model": settings.llm_model,
            "message": f"LLM_API_KEY environment variable is not set for {provider}."
        }

