import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_service.main import app, agents, agent_os



def test_debug_as():
    print(agent_os)
    assert len(agent_os.agents) >= 2