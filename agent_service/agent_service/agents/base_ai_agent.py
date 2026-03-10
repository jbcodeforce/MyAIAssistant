""""
The main agent to route to other agents, use tools and existing
knowledge.
"""

import logging
from agent_service.agents.agent_config import AgentConfig, get_llm_base_url, get_llm_model, get_vstore_path, get_llm_api_key
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from textwrap import dedent
from agent_service.ai_db import get_ai_db, create_knowledge

logger = logging.getLogger(__name__)

def  _load_system_prompt(config):
    prompt_path = config.agent_dir / "prompt.md"
    if prompt_path.exists():
        try:
            prompt_text = prompt_path.read_text()
            logger.debug(f"Loaded prompt from filesystem for agent: {config.name}")
            return dedent(prompt_text).strip()
        except Exception as e:
            logger.error(f"Failed to load prompt for {config.name}: {e}")
            return "You are a helpful assistant."
    else:
        return "You are a helpful assistant."

def _build_model():
    base_url = get_llm_base_url()
    model = get_llm_model()
    return OpenAILike(
        id=model,
        base_url=base_url,
        temperature=0.2,
        api_key=get_llm_api_key(),
    )

class AIAgent:
     
    def __init__(self,  config: AgentConfig):
        self._config = config
        self._system_prompt = _load_system_prompt(self._config)
        self._knowledge = create_knowledge(self._config.knowledge_name, self._config.knowledge_name)
        self._agent = Agent(
            id=self._config.name,
            name=self._config.name,
            model=_build_model(),
            instructions=self._system_prompt,
            db=get_ai_db(),
            knowledge=self._knowledge,
            search_knowledge=(self._knowledge is not None),
            add_datetime_to_context=True,
            add_history_to_context=True,
            num_history_runs=3,
            markdown=True,
            reasoning=True,
            telemetry=False
        )


    def get_agent(self):
        return self._agent
    
    def get_system_prompt(self):
        return self._system_prompt

    