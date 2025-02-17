"""Options tab implementation."""
from textual.containers import Container, Vertical
from textual.widgets import Static, Button
from textual.screen import ModalScreen
from textual import on
from asyncio import sleep

from .widgets.ai_config import AIConfigWidget
from .widgets.saving_popup import SavingPopup

class OptionsTab(Container):
    """Options tab content."""
    
    def compose(self):
        """Create child widgets for the app."""
        with Vertical():
            yield Static("AI Configuration", classes="tab-section-title")
            yield AIConfigWidget("Expert", "expert")
            yield AIConfigWidget("Reviewer", "reviewer")
            yield Button("Save Settings", variant="primary", id="save-settings")

    @on(Button.Pressed, "#save-settings")
    async def handle_save(self):
        """Handle save button press."""
        popup = SavingPopup()
        self.app.push_screen(popup)
        await sleep(2)
        self.app.pop_screen() 