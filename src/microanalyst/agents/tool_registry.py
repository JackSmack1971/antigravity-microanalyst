from typing import Callable, Dict, Any, List

class ToolRegistry:
    """
    Centralized registry for agent tools.
    Allows agents to discover and execute capabilities (Tech 5).
    """
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._descriptions: Dict[str, str] = {}
        
    def register(self, name: str, func: Callable, description: str):
        """Registers a new tool."""
        self._tools[name] = func
        self._descriptions[name] = description
        
    def get_tool(self, name: str) -> Callable:
        """Retrieves a tool by name."""
        return self._tools.get(name)
        
    def list_tools(self) -> str:
        """Returns a formatted list of available tools for prompt injection."""
        listing = ""
        for name, desc in self._descriptions.items():
            listing += f"- {name}: {desc}\n"
        return listing
    
    def execute(self, tool_name: str, **kwargs) -> Any:
        """Safely executes a tool."""
        if tool_name not in self._tools:
            return f"Error: Tool '{tool_name}' not found."
        try:
            return self._tools[tool_name](**kwargs)
        except Exception as e:
            return f"Error executing '{tool_name}': {str(e)}"
