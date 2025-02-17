"""Expert tab implementation."""
from textual.containers import Container
from textual.widgets import Static

class ExpertTab(Container):
    """Expert tab content."""
    
    def compose(self):
        yield Static("Expert Settings", classes="tab-title") 