""""
Given a taks description as persisted in the database todo table, the agent performs task analysis
and returns recommendations, may be to create a new project, searches knowledge, search the web, 
creates another task or an asset.

For new project, asset or task, it requests human confirmation before creating project/asset/task. Example task
data uses biz-db-like shape (backend Todo).
"""

import logging
from typing import List, Optional

from agent_service.agents.agent_config import AgentConfig, get_llm_base_url, get_llm_api_key
from agent_service.tools.backend_tools import TASK_PROJECT_TOOL_REGISTRY
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from textwrap import dedent
from agent_service.ai_db import get_ai_db, create_knowledge
from agent_service.agents.base_ai_agent import _load_system_prompt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Todo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str = "Open"
    urgency: Optional[str] = None
    importance: Optional[str] = None
    project_id: Optional[int] = None
    

class TaskAgent:
     
    def __init__(self,  config: AgentConfig):
        self._config = config
        self._system_prompt = _load_system_prompt(self._config)
        self._knowledge = create_knowledge(self._config.knowledge_name, self._config.knowledge_name)
        _model =  OpenAILike(
                id=self._config.model,
                base_url=get_llm_base_url(),
                temperature=self._config.temperature,
                api_key=get_llm_api_key(),
        )
        #tools = _resolve_tools(getattr(self._config, "tools", None))
        self._agent = Agent(
            id=self._config.name,
            name=self._config.name,
            description=self._config.description,
            model=_model,
            instructions=self._system_prompt,
            db=get_ai_db(),
            knowledge=self._knowledge,
            search_knowledge=(self._knowledge is not None),
            input_schema=Todo,
        )


    def get_agent(self):
        return self._agent
    
    def get_system_prompt(self):
        return self._system_prompt

    