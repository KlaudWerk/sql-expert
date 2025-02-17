"""Database tab implementation."""
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, RichLog, Button
from textual import on
from expert.tool.connection import DatabaseConnection
import traceback
import pyperclip
from rich.text import Text
from functools import partial

from .widgets.database_panel import DatabaseConnectionPanel

class DatabaseTab(Container):
    """Database tab content."""
    
    def compose(self):
        with Horizontal():
            # Left Panel
            with Vertical(classes="left-panel"):
                yield DatabaseConnectionPanel()
            
            # Right Panel
            with Vertical(classes="right-panel"):
                # Log header with buttons
                with Horizontal(classes="log-header"):
                    yield Static("Connection Log", classes="section-title")
                    with Horizontal(classes="log-buttons"):
                        yield Button("Copy", id="copy-log", variant="default")
                        yield Button("Clear", id="clear-log", variant="default")
                yield RichLog(wrap=True, id="db-log")

    def on_mount(self):
        """Initialize the log when the tab is mounted."""
        log = self.query_one("#db-log")
        log.write("Ready to connect...")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if button_id == "clear-log":
            self.handle_clear_log()
        elif button_id == "copy-log":
            self.handle_copy_log()

    def handle_clear_log(self):
        """Handle clear log button press."""
        log = self.query_one("#db-log")
        log.clear()
        log.write("Log cleared...")

    def handle_copy_log(self):
        """Handle copy log button press."""
        log = self.query_one("#db-log")
        
        # Get log content and copy to clipboard
        log_content = []
        for segment in log.lines:
            if isinstance(segment, Text):
                log_content.append(segment.plain)
            else:
                log_content.append(str(segment))
        
        # Join lines and copy to clipboard
        text_to_copy = "\n".join(log_content)
        pyperclip.copy(text_to_copy)
        
        # Show confirmation
        log.write("[green]Log copied to clipboard![/green]")

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

    async def on_database_connection_panel_connect_clicked(self, message: DatabaseConnectionPanel.ConnectClicked):
        """Handle connect button click from panel."""
        await self.app.action_connect_database(message.params)

    async def on_database_connection_panel_connect_save_clicked(self, message: DatabaseConnectionPanel.ConnectSaveClicked):
        """Handle connect and save button click from panel."""
        await self.app.action_connect_save_database(message.params)

    async def action_connect_database(self, params: dict) -> None:
        """Action to handle database connection."""
        log = self.query_one("#db-log")
        log.clear()
        
        try:
            # Log connection attempt
            log.write(Text("Attempting database connection...", style="yellow"))
            log.write(Text(f"Type: {params['db_type']}", style="yellow"))
            log.write(Text(f"Host: {params['host']}", style="yellow"))
            log.write(Text(f"Database: {params['database']}", style="yellow"))
            log.write(Text(f"Username: {params['username']}", style="yellow"))
            log.write("") # Empty line for readability
            
            # Get singleton instance and connect
            connection = DatabaseConnection()
            await connection.connect(
                db_type=params['db_type'],
                host=params['host'],
                database=params['database'],
                username=params['username'],
                password=params['password']
            )
            
            # Log success
            log.write(Text("Successfully connected to database!", style="green"))
            
            # Log additional connection info
            if connection.db_info:
                log.write("")  # Empty line for readability
                log.write(Text("Connection Details:", style="green"))
                log.write(Text(str(connection.db_info), style="green"))
                
                # Log table information
                if connection.db_info.tables:
                    log.write("")  # Empty line for readability
                    log.write(Text("Tables:", style="green bold"))
                    for table_name, table_info in connection.db_info.tables.items():
                        log.write("")  # Empty line for better readability
                        log.write(Text(f"📋 {table_name}", style="green bold"))
                        
                        # Show columns
                        if 'columns' in table_info:
                            # First, find primary key columns
                            pk_columns = {col['name'] for col in table_info['columns'] if col.get('primary_key', False)}
                            
                            # Find columns that are part of foreign keys (as source columns)
                            fk_source_columns = set()
                            for fk in table_info.get('foreign_keys', []):
                                fk_source_columns.update(fk['constrained_columns'])
                            
                            # Show columns with their details
                            for column in table_info['columns']:
                                col_name = column['name']
                                col_type = column['type']
                                nullable = "NULL" if column.get('nullable', True) else "NOT NULL"
                                
                                # Add indicators
                                indicators = []
                                if col_name in pk_columns:
                                    indicators.append("🔑")  # Primary key
                                if col_name in fk_source_columns:
                                    indicators.append("🔗")  # Foreign key
                                if column.get('autoincrement', False):
                                    indicators.append("🔄")  # Auto increment
                                
                                # Format the column line
                                indicator_str = " ".join(indicators)
                                if indicator_str:
                                    indicator_str += " "
                                
                                log.write(Text(f"  {indicator_str}{col_name}: {col_type} {nullable}", style="green"))
                        
                        # Show foreign key relationships
                        if table_info.get('foreign_keys'):
                            log.write(Text("  Foreign Key Relationships:", style="green bold"))
                            for fk in table_info['foreign_keys']:
                                ref_table = fk['referred_table']
                                for local_col, ref_col in zip(fk['constrained_columns'], fk['referred_columns']):
                                    log.write(Text(f"    🔗 {local_col} → {ref_table}.{ref_col}", style="green"))
                                    
                                # Show ON UPDATE/DELETE if present
                                if 'options' in fk and fk['options']:
                                    options = []
                                    if 'onupdate' in fk['options']:
                                        options.append(f"ON UPDATE {fk['options']['onupdate']}")
                                    if 'ondelete' in fk['options']:
                                        options.append(f"ON DELETE {fk['options']['ondelete']}")
                                    if options:
                                        log.write(Text(f"      ({', '.join(options)})", style="green dim"))
        
        except Exception as e:
            # Log error
            ex = traceback.format_exc()
            log.write(Text("Error connecting to database:", style="red bold"))
            log.write("")  # Empty line for readability
            log.write(Text(ex, style="red"))

    async def action_connect_save_database(self, params: dict) -> None:
        """Action to handle database connection and save."""
        log = self.query_one("#db-log")
        log.clear()
        
        try:
            log.write(Text("Testing connection before saving...", style="yellow"))
            log.write(Text(f"Type: {params['db_type']}", style="yellow"))
            log.write(Text(f"Host: {params['host']}", style="yellow"))
            log.write(Text(f"Database: {params['database']}", style="yellow"))
            log.write(Text(f"Username: {params['username']}", style="yellow"))
            log.write("") # Empty line for readability
            
            # Get singleton instance and connect
            connection = DatabaseConnection()
            await connection.connect(
                db_type=params['db_type'],
                host=params['host'],
                database=params['database'],
                username=params['username'],
                password=params['password']
            )
            
            # Log success and connection info
            log.write(Text("Successfully connected to database!", style="green"))
            if connection.db_info:
                log.write("")  # Empty line for readability
                log.write(Text("Connection Details:", style="green"))
                log.write(Text(str(connection.db_info), style="green"))
            
            log.write("")  # Empty line for readability
            log.write(Text("Note: Configuration saving not yet implemented", style="yellow"))
            
        except Exception as e:
            # Log error
            ex = traceback.format_exc()
            log.write(Text("Error connecting to database:", style="red bold"))
            log.write("")  # Empty line for readability
            log.write(Text(ex, style="red")) 