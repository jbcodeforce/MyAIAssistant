"""Task planning agent for task-related queries."""

import logging
from typing import Optional

from agent_core.agents.base_agent import BaseAgent, AgentResponse, AgentInput
from agent_core.services.rag.service import RAGService, get_rag_service

logger = logging.getLogger(__name__)


class TaskAgent(BaseAgent):
    """
    Agent specialized in task planning and management.
    
    Helps users plan, organize, and break down tasks into
    actionable steps.
    """
    
    agent_type = "task"
    
    def __init__(
        self,
        rag_service: RAGService = None,
        use_rag: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.rag_service = rag_service or get_rag_service()
        self.use_rag = use_rag

    async def execute(
        self,
        input_data: AgentInput
    ) -> AgentResponse:
        """Execute task planning with optional RAG context."""
        context = input_data.context or {}
        context_used = []
        rag_context = ""
        
        # Get task context if provided
        task_title = context.get("task_title")
        task_description = context.get("task_description")
        
        # Determine if RAG should be used (input_data.use_rag overrides instance setting)
        use_rag = input_data.use_rag if input_data.use_rag is not None else self.use_rag
        
        # Optionally search for relevant context
        if use_rag:
            search_query = task_title or input_data.query
            rag_results = await self.rag_service.search(search_query, n_results=3)
            
            if rag_results:
                context_parts = []
                for result in rag_results:
                    context_parts.append(f"[From: {result.title}]\n{result.content}")
                    context_used.append({
                        "title": result.title,
                        "uri": result.uri,
                        "score": result.score,
                        "snippet": (
                            result.content[:200] + "..." 
                            if len(result.content) > 200 
                            else result.content
                        )
                    })
                rag_context = "\n\n---\n\n".join(context_parts)

        # Build messages
        system_prompt = self.build_system_prompt({
            "task_title": task_title,
            "task_description": task_description,
            "rag_context": rag_context
        })
        messages = [{"role": "system", "content": system_prompt}]
        
        if input_data.conversation_history:
            for msg in input_data.conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        messages.append({"role": "user", "content": input_data.query})
        
        # Generate response
        response_text = await self._call_llm(messages)
        
        return AgentResponse(
            message=response_text,
            context_used=context_used,
            model=self.model,
            provider="huggingface",
            agent_type=self.agent_type,
            metadata={
                "task_title": task_title,
                "rag_used": use_rag
            }
        )

    def build_system_prompt(self, context: Optional[dict] = None) -> str:
        """Build system prompt for task planning agent."""
        context = context or {}
        task_title = context.get("task_title")
        task_description = context.get("task_description")
        rag_context = context.get("rag_context", "")
        
        prompt_parts = [
            "You are a helpful AI assistant that helps users plan and execute tasks.",
            "You provide clear, actionable advice and break down complex tasks into manageable steps.",
        ]
        
        if task_title:
            prompt_parts.extend([
                "",
                "## Current Task",
                f"**Title:** {task_title}"
            ])
            if task_description:
                prompt_parts.append(f"**Description:** {task_description}")
        
        if rag_context:
            prompt_parts.extend([
                "",
                "## Relevant Knowledge Base Context",
                "Use this context to provide informed advice:",
                "",
                rag_context
            ])
        
        prompt_parts.extend([
            "",
            "## Instructions",
            "- Help the user understand how to approach and complete the task",
            "- Break down complex tasks into clear, actionable steps",
            "- Provide time estimates when appropriate",
            "- Identify potential blockers or dependencies",
            "- Reference the knowledge base context when relevant",
            "- Ask clarifying questions if needed"
        ])
        
        return "\n".join(prompt_parts)

