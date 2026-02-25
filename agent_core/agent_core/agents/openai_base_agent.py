
from openai import OpenAI
from typing import Optional
from agent_core.agents.agent_config import AgentConfig
from agent_core.agents.base_agent import BaseAgent, AgentInput, AgentResponse

class OpenAIAgent(BaseAgent):

    def __init__(self,  config: Optional[AgentConfig] = None):
        self._config = config
        self._llm_client = OpenAI(
            api_key=self._config.api_key,
            base_url=self._config.base_url
        )
        self.agent_type = self._config.name or "OpenAIBaseAgent"
        if self._config.sys_prompt is None:
            self._config.sys_prompt = self._load_system_prompt()
    

    async def execute(
        self,
        input_data: AgentInput
    ) -> AgentResponse:
        messages = [
            {"role": "system", "content": self._config.sys_prompt},
            {"role": "user", "content": input_data.query}
        ]
        print(f"Sending messages to LLM: {messages}",flush=True)
        response =  self._llm_client.chat.completions.create(messages=messages, model=self._config.model)
        content= response.choices[0].message.content
        context_used = [input_data.context]
        return AgentResponse(
            message=content,
            context_used=context_used,
            agent_type=self.agent_type,
        )