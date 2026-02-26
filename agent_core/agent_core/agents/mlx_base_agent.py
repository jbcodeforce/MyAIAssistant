from typing import Optional
import os
from mlx_lm import load, generate
from agent_core.agents.agent_config import AgentConfig
from agent_core.agents.base_agent import BaseAgent, AgentInput, AgentResponse

class MLXBaseAgent(BaseAgent):

    def __init__(self,  config: Optional[AgentConfig] = None):
        self._config = config
        self._model, self._tokenizer = load(self._config.model)

        self.agent_type = self._config.name or "MLXBaseAgent"
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
        prompt =  self._tokenizer.apply_chat_template(conversation=messages, add_generation_prompt=True)
        text = generate(self._model, 
                self._tokenizer, 
                prompt=prompt, 
                verbose=True)
        return AgentResponse(
            message=text,
            context_used=[input_data.context],
            agent_type=self.agent_type,
        )