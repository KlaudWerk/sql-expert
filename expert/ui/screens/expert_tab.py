"""Expert tab implementation."""
from textual.widgets import RichLog, Button, Checkbox, Static, TextArea
from textual.containers import Horizontal, Vertical, Container, VerticalScroll
from textual.binding import Binding
from textual import events
from textual.message import Message

class SendMessage(Message):
    """Message sent when text needs to be processed."""
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()

class ConnectionStatus(Static):
    """Widget to show database connection status."""
    def update_status(self, is_connected: bool, params: dict = None):
        if is_connected:
            db_info = f"Connected to: {params.get('database', 'N/A')} @ {params.get('host', 'N/A')}"
            self.styles.color = "green"
            self.update(f"✓ {db_info}")
        else:
            self.styles.color = "red"
            self.update("✗ Not connected to database")

class MessageInput(TextArea):
    """Custom TextArea that handles Enter key."""

    def on_key(self, event: events.Key) -> None:
        """Handle key events."""
        if event.key == "enter":
            if "shift" in event.name or "upper" in event.name:
                return
            text = self.text.strip()
            if text:  # Only proceed if there's text to send
                event.prevent_default()
                self.clear()
                # Post message to the message bus
                self.post_message(SendMessage(text))

class ExpertTab(Static):
    """Expert system interaction tab."""

    def compose(self):
        """Create child widgets for the tab."""
        yield VerticalScroll(
            Container(
                Checkbox("Enable Reviewer", id="reviewer-checkbox"),
                ConnectionStatus("✗ Not connected to database", id="connection-status"),
                RichLog(id="expert-log", wrap=False),
                Horizontal(
                    MessageInput(
                        id="message-input",
                        disabled=False
                    ),
                    Button(
                        "Enter",
                        id="send-button",
                        disabled=False,
                        variant="primary"
                    ),
                    id="input-container",
                )
            )
        )

    def on_mount(self) -> None:
        """Handle the tab mount event."""
        self.log_widget = self.query_one("#expert-log")
        self.input = self.query_one("#message-input")
        self.send_button = self.query_one("#send-button")
        self.log_widget.write("Welcome to Expert System!")

    def on_send_message(self, message: SendMessage) -> None:
        """Handle send message events."""
        self.log_widget.write(message.text)
        self.log_widget.write("Sending...")
        # Here you can add your processing logic
        self.log_widget.write("Sent")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "send-button":
            input_widget = self.query_one("#message-input")
            text = input_widget.text
            input_widget.clear()
            # Use the same message bus for button presses
            self.post_message(SendMessage(text))

    def update_connection_status(self, is_connected: bool, params: dict = None):
        """Update the connection status display."""
        status = self.query_one(ConnectionStatus)
        status.update_status(is_connected, params)
        
        # Enable/disable input controls based on connection status
        self.query_one("#message-input").disabled = not is_connected
        self.query_one("#send-button").disabled = not is_connected