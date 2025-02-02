from typing import Optional, List, Dict, Any, Protocol, Tuple, AsyncIterator, AsyncGenerator, TypedDict
from dataclasses import dataclass
from abc import abstractmethod

class AIMessageDict(TypedDict):
    """Type definition for AI messages."""
    role: str
    content: str

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
    async def ask(
        self,
        message: str,
        history: List[AIMessageDict]
    ) -> AIResponse:
        """Ask AI expert a question."""
        pass

    @abstractmethod
    async def stream(
        self,
        message: str,
        history: List[AIMessageDict]
    ) -> AsyncGenerator[str, None]:
        """Stream AI expert's response."""
        pass 