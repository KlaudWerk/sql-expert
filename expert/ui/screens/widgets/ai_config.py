"""AI configuration widget implementation."""
from textual.containers import Container, Vertical
from textual.widgets import Static, Input, Select, Label

class AIConfigWidget(Container):
    """Widget for AI model configuration."""
    
    def __init__(self, title: str, id_prefix: str):
        super().__init__()
        self.title = title
        self.id_prefix = id_prefix

    def compose(self):
        with Vertical():
            yield Static(f"{self.title} Configuration", classes="section-title")
            
            yield Label("AI Model")
            yield Select(
                options=[
                    ("GPT-4", "gpt-4"),
                    ("GPT-3.5", "gpt-3.5-turbo"),
                    ("Claude 3 Opus", "claude-3-opus"),
                    ("Claude 3 Sonnet", "claude-3-sonnet"),
                ],
                value="gpt-4",
                id=f"{self.id_prefix}-model"
            )
            
            yield Label("API Key")
            yield Input(
                value="",
                password=True,
                placeholder="Enter API key...",
                id=f"{self.id_prefix}-key"
            ) 