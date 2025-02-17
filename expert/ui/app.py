"""Main application module."""
from textual.app import App
from textual.widgets import Header, Footer, TabbedContent, TabPane
from expert.ui.screens import OptionsTab, DatabaseTab, ExpertTab
from expert.ui.styles import CUSTOM_CSS

class MyTUI(App):
    """Main application class."""
    
    TITLE = "Expert System"  # This will show in the header
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    CSS = CUSTOM_CSS

    def compose(self):
        """Create child widgets for the app."""
        yield Header()
        with TabbedContent(initial="tab-database"):
            with TabPane("⚙️ Options", id="tab-options"):
                yield OptionsTab()
            with TabPane("🗄️ Database", id="tab-database"):
                yield DatabaseTab()
            with TabPane("🤖 Expert", id="tab-expert"):
                yield ExpertTab()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    async def action_connect_database(self, params: dict) -> None:
        """Action to connect to database."""
        tab = self.query_one(DatabaseTab)
        await tab.action_connect_database(params)

    async def action_connect_save_database(self, params: dict) -> None:
        """Action to connect and save database configuration."""
        tab = self.query_one(DatabaseTab)
        await tab.action_connect_save_database(params)

def run():
    """Run the application."""
    app = MyTUI()
    app.run()

if __name__ == "__main__":
    run() 