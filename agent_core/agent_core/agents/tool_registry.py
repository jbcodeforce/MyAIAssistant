from typing import Callable, Dict, Any

class ToolRegistry:
    """A registry for managing callable tools."""

    def __init__(self):
        self._tools: Dict[str, Callable[..., Any]] = {}

    def register_tool(self, name: str, func: Callable[..., Any]):
        """Register a callable function as a tool."""
        if not callable(func):
            raise ValueError(f"Tool '{name}' must be a callable function.")
        self._tools[name] = func

    def get_tool(self, name: str) -> Callable[..., Any]:
        """Retrieve a registered tool by its name."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found in registry.")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        """List the names of all registered tools."""
        return list(self._tools.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __getitem__(self, name: str) -> Callable[..., Any]:
        return self.get_tool(name)

# Global tool registry instance
_global_tool_registry = ToolRegistry()

def get_global_tool_registry() -> ToolRegistry:
    """Returns the global tool registry instance."""
    return _global_tool_registry

def tool(name: str):
    """Decorator to register a function as a tool in the global registry."""
    def decorator(func: Callable[..., Any]):
        get_global_tool_registry().register_tool(name, func)
        return func
    return decorator
