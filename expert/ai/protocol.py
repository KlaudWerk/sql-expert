from typing import Optional, List, Dict, Any, Protocol, Tuple
from dataclasses import dataclass
from abc import abstractmethod

@dataclass
class AIResponse:
    """Class to hold AI response data."""
    message: str
    result_set: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class AIExpertProtocol(Protocol):
    """Protocol for AI expert interactions."""
    
    @abstractmethod
    def __init__(self, api_key: str, model: str, system_prompt: Optional[str] = None):
        """Initialize AI expert with API key, model, and optional system prompt."""
        pass
    
    @abstractmethod
    def init(self, ddl: str) -> None:
        """Initialize AI expert with database DDL."""
        pass
    
    @abstractmethod
    def ask(
        self,
        message: str,
        history: List[Tuple[str, str]]
    ) -> AIResponse:
        """Ask AI expert a question."""
        pass 