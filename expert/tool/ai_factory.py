from typing import Optional
from .ai_protocol import AIExpertProtocol, OpenAIExpert, AnthropicExpert

class AIFactory:
    """Factory for creating AI experts."""
    
    @staticmethod
    def create_expert(
        expert_type: str,
        api_key: str,
        model: Optional[str] = None
    ) -> AIExpertProtocol:
        """
        Create an AI expert instance.
        
        Args:
            expert_type: Type of expert ("openai" or "anthropic")
            api_key: API key for the service
            model: Optional model name
            
        Returns:
            AIExpertProtocol implementation
        """
        if expert_type.lower() == "openai":
            return OpenAIExpert(api_key, model or "gpt-4")
        elif expert_type.lower() == "anthropic":
            return AnthropicExpert(api_key, model or "claude-3-sonnet-20240229")
        else:
            raise ValueError(f"Unsupported AI expert type: {expert_type}") 