"""Saving popup implementation."""
from textual.screen import ModalScreen
from textual.containers import Container
from textual.widgets import Static, LoadingIndicator

class SavingPopup(ModalScreen):
    """A modal screen that shows a loading indicator."""
    
    def compose(self):
        yield Container(
            LoadingIndicator(),
            Static("Saving...", id="saving-text"),
            classes="popup-dialog"
        ) 