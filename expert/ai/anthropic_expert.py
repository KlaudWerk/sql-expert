from typing import Optional, List, Tuple, Dict, AsyncIterator, AsyncGenerator
from .protocol import AIResponse, AIExpertProtocol, AIMessageDict
import traceback
from anthropic import AsyncAnthropic

class AnthropicExpert(AIExpertProtocol):
    """Anthropic-based expert implementation."""
    
    def __init__(
        self,
        api_key: str,
        system_prompt: str,
        model: str = "claude-3-sonnet-20240229",
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.ddl: Optional[str] = None
        self.system_prompt = system_prompt 
    
    def init(self, ddl: str) -> None:
        self.ddl = ddl
    
    async def stream(
        self,
        message: str,
        history: List[AIMessageDict]
    ) -> AsyncGenerator[str, None]:
        """Stream AI expert's response."""
        if not self.ddl:
            yield "I haven't been initialized with database structure yet."
            return

        messages = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": message})

        try:
            stream = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=f"{self.system_prompt}\nDatabase DDL:\n{self.ddl}",
                messages=messages,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.content:
                    yield chunk.content[0].text
                    
        except Exception as e:
            traceback.print_exc()
            print(f"Streaming error: {str(e)}")
            yield f"\nError during streaming: {str(e)}"
    
    async def ask(
        self,
        message: str,
        history: List[AIMessageDict]
    ) -> AIResponse:
        if not self.ddl:
            return AIResponse(
                message="I haven't been initialized with database structure yet.",
                error="Not initialized"
            )
        
        messages = []
        
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        try:
            # Stream the response and concatenate chunks
            full_response = ""
            async for chunk in self.stream(message, history):
                full_response += chunk
            
            return AIResponse(
                message=full_response
            )           

        except Exception as e:
            traceback.print_exc()
            print(f"Error: {str(e)}")
            return AIResponse(
                message="Sorry, I encountered an error.",
                error=str(e)
            ) 