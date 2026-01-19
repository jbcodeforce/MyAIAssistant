"""Code assistance agent for programming-related queries."""

import logging
from typing import Optional

from agent_core.agents.base_agent import BaseAgent, AgentResponse, AgentInput
from agent_core.services.rag.service import RAGService, get_rag_service

logger = logging.getLogger(__name__)


class CodeAgent(BaseAgent):
    """
    Agent specialized in code assistance and technical help.
    
    Helps with programming questions, code review, debugging,
    and technical implementation guidance.
    """
    
    agent_type = "code"
    
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
        """Execute code assistance with optional RAG context."""
        context = input_data.context or {}
        context_used = []
        rag_context = ""
        
        # Extract programming context from entities
        entities = context.get("entities", {})
        language = entities.get("language")
        framework = entities.get("framework")
        
        # Determine if RAG should be used (input_data.use_rag overrides instance setting)
        use_rag = input_data.use_rag if input_data.use_rag is not None else self.use_rag
        
        # Search for relevant documentation if available
        if use_rag:
            search_terms = [input_data.query]
            if language:
                search_terms.append(language)
            if framework:
                search_terms.append(framework)
            
            search_query = " ".join(search_terms)
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
            "language": language,
            "framework": framework,
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
                "language": language,
                "framework": framework,
                "rag_used": use_rag
            }
        )

    def build_system_prompt(self, context: Optional[dict] = None) -> str:
        """Build system prompt for code agent."""
        context = context or {}
        language = context.get("language")
        framework = context.get("framework")
        rag_context = context.get("rag_context", "")
        
        prompt_parts = [
            "You are an expert programming assistant.",
            "You help with code review, debugging, implementation, and technical questions.",
        ]
        
        if language or framework:
            prompt_parts.append("")
            prompt_parts.append("## Technical Context")
            if language:
                prompt_parts.append(f"**Primary Language:** {language}")
            if framework:
                prompt_parts.append(f"**Framework:** {framework}")
        
        if rag_context:
            prompt_parts.extend([
                "",
                "## Relevant Documentation",
                rag_context
            ])
        
        prompt_parts.extend([
            "",
            "## Instructions",
            "- Provide clear, well-structured code examples",
            "- Explain your reasoning and approach",
            "- Follow best practices and coding standards",
            "- Consider edge cases and error handling",
            "- Suggest tests when appropriate",
            "- Reference documentation when available"
        ])
        
        return "\n".join(prompt_parts)

