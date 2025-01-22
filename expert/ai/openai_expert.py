from typing import Optional, List, Tuple
from .protocol import AIResponse, AIExpertProtocol
import traceback

class OpenAIExpert(AIExpertProtocol):
    """OpenAI-based expert implementation."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        system_prompt: Optional[str] = None
    ):
        import openai
        openai.api_key = api_key
        self.client = openai.OpenAI()
        self.model = model
        self.ddl: Optional[str] = None
        self.system_prompt = system_prompt or """
You are a database expert. You help users understand their database structure and write SQL queries.
You have access to the database DDL which will be provided in the initialization.
When users ask for queries, you should return both an explanation and the SQL query.
"""
    
    def init(self, ddl: str) -> None:
        self.ddl = ddl
    
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
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Database DDL:\n{self.ddl}"}
        ]
        
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            return AIResponse(
                message=response.choices[0].message.content
            )
            
        except Exception as e:
            traceback.print_exc()
            print(f"Error: {str(e)}")
            return AIResponse(
                message="Sorry, I encountered an error.",
                error=str(e)
            ) 