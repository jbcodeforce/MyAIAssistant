"""RAG-based agent for knowledge search queries."""

import logging
from typing import Optional

from agent_core.agents.base_agent import BaseAgent, AgentResponse
from agent_core.services.rag.service import RAGService, get_rag_service

logger = logging.getLogger(__name__)


class RAGAgent(BaseAgent):
    """
    Agent specialized in knowledge base search and retrieval.
    
    Uses RAG to find relevant documents and answers questions
    based on indexed knowledge.
    """
    
    agent_type = "rag"
    
    def __init__(
        self,
        rag_service: RAGService = None,
        n_results: int = 5,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.rag_service = rag_service or get_rag_service()
        self.n_results = n_results

    async def execute(
        self,
        query: str,
        conversation_history: Optional[list[dict]] = None,
        context: Optional[dict] = None
    ) -> AgentResponse:
        """Execute RAG search and generate response."""
        context = context or {}
        context_used = []
        rag_context = ""
        
        # Get search keywords from entities if available
        search_query = query
        if context.get("entities"):
            keywords = context["entities"].get("keywords", [])
            topic = context["entities"].get("topic")
            if topic:
                search_query = f"{topic} {query}"
            elif keywords:
                search_query = f"{' '.join(keywords)} {query}"
        
        # Search knowledge base
        rag_results = await self.rag_service.search(
            search_query, 
            n_results=self.n_results
        )
        
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
        system_prompt = self.build_system_prompt({"rag_context": rag_context})
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        messages.append({"role": "user", "content": query})
        
        # Generate response
        response_text = await self._call_llm(messages)
        
        return AgentResponse(
            message=response_text,
            context_used=context_used,
            model=self.model,
            provider=self.provider,
            agent_type=self.agent_type,
            metadata={
                "search_query": search_query,
                "results_count": len(rag_results) if rag_results else 0
            }
        )

    def build_system_prompt(self, context: Optional[dict] = None) -> str:
        """Build system prompt for RAG agent."""
        context = context or {}
        rag_context = context.get("rag_context", "")
        
        prompt_parts = [
            "You are a helpful AI assistant with access to a knowledge base.",
            "Answer the user's questions using the provided context from the knowledge base.",
            "If the context doesn't contain relevant information, say so clearly.",
        ]
        
        if rag_context:
            prompt_parts.extend([
                "",
                "## Knowledge Base Context",
                "Use this context to answer the user's question:",
                "",
                rag_context
            ])
        else:
            prompt_parts.extend([
                "",
                "## Note",
                "No relevant context was found in the knowledge base for this query.",
                "Inform the user that the answer is not based on their indexed documents."
            ])
        
        prompt_parts.extend([
            "",
            "## Instructions",
            "- Answer questions based on the provided context",
            "- Cite the source document when referencing specific information",
            "- Be concise and accurate",
            "- If the context is insufficient, acknowledge the limitation"
        ])
        
        return "\n".join(prompt_parts)

