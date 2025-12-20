from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """
    Abstract base class for all analytic agents.
    Defines a consistent interface for task execution and context processing.
    """
    
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's specialized logic based on the provided context.
        """
        pass
