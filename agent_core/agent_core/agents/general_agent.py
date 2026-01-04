"""General conversation agent for non-specific queries."""

import logging
from typing import Optional

from agent_core.agents.base_agent import BaseAgent, AgentResponse

logger = logging.getLogger(__name__)


class GeneralAgent(BaseAgent):
    """
    Agent for general conversation and queries.
    
    Handles queries that don't fit into specialized categories.
    """
    
    agent_type = "general"

    async def execute(
        self,
        query: str,
        conversation_history: Optional[list[dict]] = None,
        context: Optional[dict] = None
    ) -> AgentResponse:
        """Execute general conversation."""
        context = context or {}
        
        # Build messages
        system_prompt = self.build_system_prompt(context)
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
            context_used=[],
            model=self.model,
            provider=self.provider,
            agent_type=self.agent_type,
            metadata={}
        )

    def build_system_prompt(self, context: Optional[dict] = None) -> str:
        """Build system prompt for general agent."""
        prompt_parts = [
            "You are a helpful AI assistant.",
            "You provide clear, accurate, and helpful responses.",
            "",
            "## Instructions",
            "- Be helpful and friendly",
            "- Provide accurate information",
            "- If you're unsure about something, say so",
            "- Keep responses concise but thorough"
        ]
        
        return "\n".join(prompt_parts)

