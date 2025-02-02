from typing import Optional, List, Tuple, AsyncIterator, AsyncGenerator
from .protocol import AIResponse, AIExpertProtocol, AIMessageDict
import traceback
import asyncio
from openai.types.chat import ChatCompletionChunk
from openai import AsyncOpenAI

class OpenAIExpert(AIExpertProtocol):
    """OpenAI-based expert implementation."""
    
    def __init__(
        self,
        api_key: str,
        system_prompt: str,
        model: str = "gpt-4o"
        
    ):
        self.client = AsyncOpenAI(api_key=api_key)
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

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"#### Database DDL:\n{self.ddl}"}
        ]
        
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": message})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            traceback.print_exc()
            print(f"Streaming error: {str(e)}")
            yield f"\nError during streaming: {str(e)}"
    
    async def ask(
        self,
        message: str,
        history: List[AIMessageDict]
    ) -> AIResponse:
        try:
            full_response = ""
            async for chunk in self.stream(message, history):
                full_response += chunk
                
            return AIResponse(message=full_response)
            
        except Exception as e:
            traceback.print_exc()
            print(f"Error: {str(e)}")
            return AIResponse(
                message="Sorry, I encountered an error.",
                error=str(e)
            ) 