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
    def init(self, ddl: str) -> None:
        """
        Initialize AI expert with database DDL.
        
        Args:
            ddl: Database DDL string
        """
        pass
    
    @abstractmethod
    async def ask(
        self,
        message: str,
        history: List[Tuple[str, str]]
    ) -> AIResponse:
        """
        Ask AI expert a question.
        
        Args:
            message: User's message
            history: Chat history as list of (user, assistant) message tuples
            
        Returns:
            AIResponse containing assistant's message and optional result set
        """
        pass

class OpenAIExpert:
    """OpenAI-based expert implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize OpenAI expert.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4)
        """
        import openai
        openai.api_key = api_key
        self.client = openai.OpenAI()
        self.model = model
        self.ddl: Optional[str] = None
        self.system_prompt = """
You are a database expert. You help users understand their database structure and write SQL queries.
You have access to the database DDL which will be provided in the initialization.
When users ask for queries, you should return both an explanation and the SQL query.
"""
    
    def init(self, ddl: str) -> None:
        """Initialize with database DDL."""
        self.ddl = ddl
    
    async def ask(
        self,
        message: str,
        history: List[Tuple[str, str]]
    ) -> AIResponse:
        """Ask OpenAI expert."""
        if not self.ddl:
            return AIResponse(
                message="I haven't been initialized with database structure yet.",
                error="Not initialized"
            )
        
        # Construct messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Database DDL:\n{self.ddl}"}
        ]
        
        # Add history
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            # Get response from OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            return AIResponse(
                message=response.choices[0].message.content
            )
            
        except Exception as e:
            return AIResponse(
                message="Sorry, I encountered an error.",
                error=str(e)
            )

class AnthropicExpert:
    """Anthropic-based expert implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        """
        Initialize Anthropic expert.
        
        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-3-sonnet)
        """
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.ddl: Optional[str] = None
        self.system_prompt = """
You are a database expert. You help users understand their database structure and write SQL queries.
You have access to the database DDL which will be provided in the initialization.
When users ask for queries, you should return both an explanation and the SQL query.
"""
    
    def init(self, ddl: str) -> None:
        """Initialize with database DDL."""
        self.ddl = ddl
    
    async def ask(
        self,
        message: str,
        history: List[Tuple[str, str]]
    ) -> AIResponse:
        """Ask Anthropic expert."""
        if not self.ddl:
            return AIResponse(
                message="I haven't been initialized with database structure yet.",
                error="Not initialized"
            )
        
        # Construct messages
        messages = []
        
        # Add history
        for user_msg, assistant_msg in history:
            messages.extend([
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg}
            ])
        
        try:
            # Get response from Anthropic
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=f"{self.system_prompt}\nDatabase DDL:\n{self.ddl}",
                messages=[*messages, {"role": "user", "content": message}]
            )
            
            return AIResponse(
                message=response.content[0].text
            )
            
        except Exception as e:
            return AIResponse(
                message="Sorry, I encountered an error.",
                error=str(e)
            ) 