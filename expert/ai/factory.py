from typing import Optional
from .protocol import AIExpertProtocol
from .openai_expert import OpenAIExpert
from .anthropic_expert import AnthropicExpert

class AIFactory:
    """Factory for creating AI experts."""
    
    @staticmethod
    def create_expert(
        expert_type: str,
        api_key: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> AIExpertProtocol:
        """Create an AI expert instance."""
        if expert_type.lower() == "openai":
            return OpenAIExpert(
                api_key=api_key,
                model=model or "gpt-4o",
                system_prompt=system_prompt
            )
        elif expert_type.lower() == "anthropic":
            return AnthropicExpert(
                api_key=api_key,
                model=model or "claude-3.5-sonnet",
                system_prompt=system_prompt
            )
        else:
            raise ValueError(f"Unsupported AI expert type: {expert_type}") 