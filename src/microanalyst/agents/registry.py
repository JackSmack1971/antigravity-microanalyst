# src/microanalyst/agents/registry.py

from typing import Dict, Any, Callable, Awaitable
from src.microanalyst.agents.schemas import AgentRole

# Type for an agent execution handler
AgentHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]

class SwarmRegistry:
    """
    Central registry for agent task handlers.
    Decouples the orchestration logic from the business logic.
    """
    def __init__(self):
        self._handlers: Dict[AgentRole, AgentHandler] = {}

    def register(self, role: AgentRole, handler: AgentHandler):
        """Register a handler for a specific agent role"""
        self._handlers[role] = handler

    def get_handler(self, role: AgentRole) -> AgentHandler:
        """Retrieve the handler for a role. Returns None if not found."""
        return self._handlers.get(role)

# Global registry instance
registry = SwarmRegistry()
