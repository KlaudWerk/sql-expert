from typing import Optional, List, Tuple, Dict
from .protocol import AIResponse, AIExpertProtocol
import traceback

class AnthropicExpert(AIExpertProtocol):
    """Anthropic-based expert implementation."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-sonnet-20240229",
        system_prompt: Optional[str] = None
    ):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.ddl: Optional[str] = None
        self.system_prompt = system_prompt or """
You are a database expert. You help users understand their database structure and write SQL queries.
You have access to the database DDL which will be provided in the initialization.
When users ask for queries, you should return both an explanation and the SQL query.
"""
    
    def init(self, ddl: str) -> None:
        self.ddl = ddl
    
    async def _create_message(self, model: str, system: str, messages: List[Dict[str, str]]):
        """Async helper for creating messages."""
        return await self.client.messages.create(
            model=model,
            max_tokens=2048,
            system=system,
            messages=messages
        )
    
    def ask(
        self,
        message: str,
        history: List[Tuple[str, str]]
    ) -> AIResponse:
        if not self.ddl:
            return AIResponse(
                message="I haven't been initialized with database structure yet.",
                error="Not initialized"
            )
        
        messages = []
        
        for user_msg, assistant_msg in history:
            messages.extend([
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg}
            ])
        
        try:
            import asyncio
            response = asyncio.run(self._create_message(
                model=self.model,
                system=f"{self.system_prompt}\nDatabase DDL:\n{self.ddl}",
                messages=[*messages, {"role": "user", "content": message}]
            ))
            
            return AIResponse(
                message=response.content[0].text
            )           

        except Exception as e:
            traceback.print_exc()
            print(f"Error: {str(e)}")
            return AIResponse(
                message="Sorry, I encountered an error.",
                error=str(e)
            ) 