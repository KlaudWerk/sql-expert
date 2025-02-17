"""Database connection panel implementation."""
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Input, Select, Button, Checkbox, Label
from textual import on
from textual.message import Message

class DatabaseConnectionPanel(Container):
    """Left panel for database connection settings."""
    
    class InputChanged(Message):
        """Input changed message."""
        
        def __init__(self, input_valid: bool) -> None:
            self.input_valid = input_valid
            super().__init__()
    
    class ConnectClicked(Message):
        """Connect button clicked message."""
        def __init__(self, params: dict) -> None:
            self.params = params
            super().__init__()
    
    class ConnectSaveClicked(Message):
        """Connect and save button clicked message."""
        def __init__(self, params: dict) -> None:
            self.params = params
            super().__init__()
    
    def compose(self):
        yield Static("Database Connection", classes="section-title")
        
        with Vertical():
            yield Label("Database Type")
            yield Select(
                options=[
                    ("PostgreSQL", "postgresql"),
                    ("MySQL", "mysql"),
                    ("SQL Server", "mssql"),
                ],
                value="postgresql",
                id="db-type"
            )
            
            yield Label("Host")  # Changed label from "Connection String"
            yield Input(
                placeholder="Enter host...",
                id="db-connection"
            )
            
            yield Label("Username")
            yield Input(
                placeholder="Enter username...",
                id="db-username"
            )
            
            yield Label("Password")
            yield Input(
                password=True,
                placeholder="Enter password...",
                id="db-password"
            )
            yield Checkbox("Save Password", id="save-password")
            
            yield Label("Database Name")
            yield Input(
                placeholder="Enter database name...",
                id="db-name"
            )
            
            with Horizontal(classes="button-container"):
                yield Button("Connect", variant="primary", id="connect-btn", classes="db-button", disabled=True)
                yield Button("Connect & Save", variant="primary", id="connect-save-btn", classes="db-button", disabled=True)

    def on_mount(self) -> None:
        """Handle mount event to set up initial button states."""
        self.validate_inputs()

    def validate_inputs(self) -> None:
        """Validate all inputs and update button states."""
        host = self.query_one("#db-connection").value
        username = self.query_one("#db-username").value
        password = self.query_one("#db-password").value
        database = self.query_one("#db-name").value
        
        # Check if all required fields are filled
        is_valid = all([
            len(host.strip()) > 0,
            len(username.strip()) > 0,
            len(password.strip()) > 0,
            len(database.strip()) > 0
        ])
        
        # Update button states
        connect_btn = self.query_one("#connect-btn")
        connect_save_btn = self.query_one("#connect-save-btn")
        connect_btn.disabled = not is_valid
        connect_save_btn.disabled = not is_valid
        
        # Post validation message
        self.post_message(self.InputChanged(is_valid))

    @on(Input.Changed)
    def handle_input_change(self) -> None:
        """Handle any input change."""
        self.validate_inputs()

    def get_connection_params(self):
        """Get connection parameters from input fields."""
        return {
            'db_type': self.query_one("#db-type").value,
            'host': self.query_one("#db-connection").value,
            'username': self.query_one("#db-username").value,
            'password': self.query_one("#db-password").value,
            'database': self.query_one("#db-name").value,
            'save_password': self.query_one("#save-password").value
        }

    @on(Button.Pressed, "#connect-btn")
    def handle_connect(self):
        """Handle connect button press."""
        params = self.get_connection_params()
        self.post_message(self.ConnectClicked(params))

    @on(Button.Pressed, "#connect-save-btn")
    def handle_connect_save(self):
        """Handle connect and save button press."""
        params = self.get_connection_params()
        self.post_message(self.ConnectSaveClicked(params)) 