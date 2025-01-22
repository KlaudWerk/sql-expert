import os
from typing import Dict, List, Tuple, Optional
from .factory import AIFactory
from .protocol import AIExpertProtocol

class AIConfig:
    """Class to manage AI configuration."""
    
    def __init__(self):
        # Load API keys from environment
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        
        # Parse models configuration from environment
        models_str = os.getenv('AI_MODELS', 'OpenAI:gpt-4o,Anthropic:claude-3.5-sonnet')
        self.models = self._parse_models(models_str)
        
        # Initialize experts
        self.expert: Optional[AIExpertProtocol] = None
        self.reviewer: Optional[AIExpertProtocol] = None
    
    def _parse_models(self, models_str: str) -> List[Tuple[str, str]]:
        """Parse models string into list of (provider, model) tuples."""
        models = []
        for model_str in models_str.split(','):
            if ':' in model_str:
                provider, model = model_str.strip().split(':')
                models.append((provider.strip(), model.strip()))
        return models
    
    def get_model_choices(self) -> List[str]:
        """Get formatted model choices for UI."""
        return [f"{provider}:{model}" for provider, model in self.models]
    
    def create_ai(
        self,
        model_str: str,
        role: str = 'expert',
        system_prompt: Optional[str] = None
    ) -> None:
        """
        Create AI instance for specified role.
        
        Args:
            model_str: Model string in format "provider:model"
            role: Either 'expert' or 'reviewer'
            system_prompt: Optional custom system prompt
        """
        if not model_str:
            return
            
        provider, model = model_str.split(':')
        api_key = self._get_api_key(provider)
        
        if not api_key:
            raise ValueError(f"No API key found for {provider}")
            
        ai_instance = AIFactory.create_expert(
            expert_type=provider,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt or AIConfig.get_default_system_prompt(role)
        )
        
        if role == 'expert':
            self.expert = ai_instance
        elif role == 'reviewer':
            self.reviewer = ai_instance
        else:
            raise ValueError(f"Invalid role: {role}")
    
    def _get_api_key(self, provider: str) -> str:
        """Get API key for provider."""
        if provider.lower() == 'openai':
            return self.openai_api_key
        elif provider.lower() == 'anthropic':
            return self.anthropic_api_key
        return ''
    
    @staticmethod
    def get_default_system_prompt(role: str) -> str:
        """Get system prompt for specified role."""
        if role == 'expert':
            return """
You are a database expert. You help users understand their database structure and write SQL queries.
You have access to the database DDL which will be provided in the initialization.
When users ask for queries, you should:
1. Explain the approach you'll take
2. Write the SQL query if needed to fully answer the user's question
3. Explain any performance considerations
4. Point out any potential issues or edge cases
SQL code must be returned in a valid SQL format.
SQL code must be incuded in ```sql``` code block.
"""
        elif role == 'reviewer':
            return """
You are a SQL code reviewer. Your job is to review the expert's responses and review the following:
1. Query correctness
2. SQL best practices
3. Performance implications
4. Security considerations
5. Edge cases that might have been missed

Be concise but thorough in your review.
The expert's response will be provided in the initialization.
The result of your review should be comprehensive and clear.
"""
        else:
            raise ValueError(f"Invalid role: {role}")
    
    @staticmethod
    def extract_sql_query(text: str) -> Optional[str]:
        """Extract SQL query from text that contains ```sql blocks."""
        import re
        sql_blocks = re.findall(r'```sql\s*(.*?)\s*```', text, re.DOTALL)
        return sql_blocks[0].strip() if sql_blocks else None 