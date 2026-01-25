"""Chat API endpoints for LLM-powered task planning."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.chat.service import ChatService, ChatMessage, get_chat_service
from app.core.config import get_settings
from app.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ContextItem
)
from agent_core.agents.query_classifier import QueryIntent
from agent_core.agents.agent_router import AgentRouter, RoutedResponse, WorkflowState, get_agent_router


router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat() -> ChatService:
    """Dependency to get the chat service."""
    return get_chat_service()


@router.post("/todo/{todo_id}", response_model=ChatResponse)
async def chat_about_todo(
    todo_id: int,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat)
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
        response = await chat_service.chat_with_todo(
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
            ]
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


@router.post("/generic", response_model=ChatResponse)
async def generic_chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat)
):
    """
    Chat using the knowledge base for context.
    
    This endpoint allows querying the general knowledge base without 
    being tied to a specific todo task. Useful for general 
    questions about indexed documents and using a query routing system.
    This endpoint classifies the user's query to determine intent,
    then routes to the appropriate specialized agent:
    
    - **knowledge_search**: RAG-based knowledge base search
    - **task_planning**: Task breakdown and planning assistance
    - **task_status**: Task status queries
    - **code_help**: Programming and technical assistance
    - **general_chat**: General conversation
    - **research**: Deep research assistance
    
    The response includes classification metadata showing which
    agent handled the request and the confidence of classification.
    """
    # Convert conversation history
    history = [
        ChatMessage(role=msg.role, content=msg.content)
        for msg in request.conversation_history
    ]
    force_intent = None
    if request.force_intent:
        try:
            force_intent = QueryIntent(request.force_intent)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid intent: {request.force_intent}"
            )
    try:
        response = await chat_service.chat_with_routing(
            user_message=request.message,
            conversation_history=history,
            context=request.context,
            force_intent=force_intent
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
            ]
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

@router.get("/health")
async def chat_health_check(chat: ChatService = Depends(get_chat)):
    """
    Check if the chat service is configured and ready.
    
    Returns the provider configuration status.
    """
    settings = get_settings()
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

