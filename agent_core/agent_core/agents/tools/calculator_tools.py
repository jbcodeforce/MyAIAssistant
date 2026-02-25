from agent_core.agents.tool_registry import tool

@tool("add")
async def add(a: float, b: float) -> float:
    """Adds two numbers together."""
    return a + b
