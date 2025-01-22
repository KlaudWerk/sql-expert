import gradio as gr
from expert.tool.connection import DatabaseConnection
from expert.ddl import DatabaseType
from expert.ai.config import AIConfig
import os
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import traceback
import asyncio

# Load environment variables
load_dotenv()

# Initialize global instances
DB = DatabaseConnection()
AI_CONFIG = AIConfig()

# Initialize default AI models
def init_default_models():
    """Initialize AI models with defaults from environment."""
    try:
        # Set expert to first available model
        if AI_CONFIG.models:
            provider, model = AI_CONFIG.models[0]
            print(f"Initializing expert model: {provider}:{model}")
            AI_CONFIG.create_ai(model_str=f"{provider}:{model}", role='expert')
            
        # Set reviewer to second available model, or first if only one exists
        if len(AI_CONFIG.models) > 1:
            provider, model = AI_CONFIG.models[1]
            print(f"Initializing reviewer model: {provider}:{model}")
            AI_CONFIG.create_ai(model_str=f"{provider}:{model}", role='reviewer')
        elif AI_CONFIG.models:
            provider, model = AI_CONFIG.models[0]
            print(f"Initializing reviewer model: {provider}:{model}")
            AI_CONFIG.create_ai(model_str=f"{provider}:{model}", role='reviewer')
            
        return True
    except Exception as e:
        print(f"Error initializing default models: {str(e)}")
        traceback.print_exc()
        return False
 

async def execute_sql(query: str) -> gr.Dataframe:
    """Execute SQL query and return formatted results."""
    if not DB.is_connected:
        return gr.Dataframe(value=[])
        
    try:
        print(f"Executing SQL query: {query}")
        query_result, rows = await DB.async_executor.fetch_all(query)
        
        if rows:
            headers = list(rows[0].keys())
            data = [[str(row[h]) for h in headers] for row in rows]
            return gr.Dataframe(value=data, headers=headers)
        
        return gr.Dataframe(value=[])
    except Exception as e:
        traceback.print_exc()
        return gr.Dataframe(value=[])

def ask_question(message: str, history: List[Dict[str, str]]) -> Tuple[Dict[str, str], str]:
    """Handle chat messages."""
    if not AI_CONFIG.expert or not AI_CONFIG.reviewer:
        return {
            "role": "assistant",
            "content": "Please select both Expert and Reviewer models first."
        }, ""
        
    try:
        # Convert history to tuples for AI protocol
        history_tuples = [(msg["content"], msg["content"]) 
                         for msg in history if msg["role"] in ["user", "assistant"]]
        
        # Get expert response
        response = AI_CONFIG.expert.ask(message, history_tuples)
        expert_message = response.message
        
        # Get reviewer response
        reviewer_response = AI_CONFIG.reviewer.ask(
            f"Review this response for accuracy and completeness:\n{expert_message}",
            []  # Empty history for reviewer
        )
        
        # Extract SQL query if present
        sql_query = AIConfig.extract_sql_query(expert_message)
        
        chat_response = {
            "role": "assistant",
            "content": f"""
Expert's response:
{expert_message}

Reviewer's comment:
{reviewer_response.message}"""
        }
        return chat_response, sql_query or ""
        
    except Exception as e:
        return {
            "role": "assistant",
            "content": f"Error: {str(e)}"
        }, ""

def connect(database: str, url: str, port: str, default_db: str, user: str, password: str) -> str:
    """Handle database connection."""
    print(f"Connecting to {database} at {url}:{port} default db [{default_db}] with user [{user}]")
    
    try:
        if DB.is_connected:
            DB.disconnect()
            
        # Convert database type
        if database == "MySQL":
            db_type = DatabaseType.MYSQL.value
            default_db = default_db or "mydb"
        elif database == "PostgreSQL":
            db_type = DatabaseType.POSTGRESQL.value
            default_db = default_db or "postgres"
        elif database == "SQLite":
            db_type = DatabaseType.SQLITE.value
            default_db = default_db or "sqlite"
        elif database == "MSSQL":
            db_type = DatabaseType.MSSQL.value
            default_db = default_db or "mssql"
        
        # Connect to database
        DB.connect(
            db_type=db_type,
            host=url,
            port=int(port) if port else None,
            database=default_db,
            username=user,
            password=password
        )
        
        # Initialize AI models with DDL if they exist
        if AI_CONFIG.expert:
            AI_CONFIG.expert.init(DB.get_ddl())
        if AI_CONFIG.reviewer:
            AI_CONFIG.reviewer.init(DB.get_ddl())
        
        return f"Connected to {database} at {url}:{port} with user {user}\nDDL:\n{DB.db_info.ddl}"
        
    except Exception as e:
        return f"Connection failed: {str(e)}"

def update_database_options(database: str) -> Tuple[str, int]:
    """Update database-specific options."""
    print(f"Updating database options for {database}")
    if database == "MySQL":        
        return "MySQL", 3306
    elif database == "PostgreSQL":
        return "PostgreSQL", 5432
    elif database == "SQLite":
        return "SQLite", 5432
    elif database == "MSSQL":
        return "MSSQL", 1433
    else:
        return "MySQL", 3306

def on_model_change(
    model: str,
    role: str,
    expert_prompt: Optional[str] = None,
    reviewer_prompt: Optional[str] = None
) -> str:
    """Handle model selection change."""
    try:
        print(f"Setting up {role} model: {model}")
        print(f"Expert prompt: {expert_prompt}")
        print(f"Reviewer prompt: {reviewer_prompt}")
        
        prompt = expert_prompt if role == 'expert' else reviewer_prompt
        AI_CONFIG.create_ai(model, role, system_prompt=prompt)
        if DB.is_connected:
            if role == 'expert':
                AI_CONFIG.expert.init(DB.get_ddl())
            else:
                AI_CONFIG.reviewer.init(DB.get_ddl())
        return f"Selected {role} model: {model}"
    except Exception as e:
        traceback.print_exc()
        print(f"Error setting up model: {str(e)}")
        return f"Error setting up model: {str(e)}"

# Create Gradio interface
with gr.Blocks() as demo:
    with gr.Row():
        # Left panel
        with gr.Column():
            # Add SQL execution section
            with gr.Accordion("SQL Execution", open=True):
                sql_input = gr.Textbox(
                    label="SQL Query",
                    placeholder="Enter SQL query to execute",
                    lines=3
                )
                execute_btn = gr.Button("Execute Query")
                sql_output = gr.Markdown(label="Query Results")
            checkbox_group = gr.CheckboxGroup(
                ["Protect (No changes)", "Anonymize PII"],
                label="Options"
            )
            with gr.Accordion("AI Settings", open=False):
                expert_prompt = gr.Textbox(
                    label="Expert System Prompt",
                    placeholder="Leave empty for default prompt",
                    lines=4
                )
                reviewer_prompt = gr.Textbox(
                    label="Reviewer System Prompt",
                    placeholder="Leave empty for default prompt",
                    lines=4
                )
            chat = gr.ChatInterface(
                ask_question,
                type="messages",
                chatbot=gr.Chatbot(
                    height=300,
                    type="messages"
                ),
                textbox=gr.Textbox(
                    placeholder="Ask me about the database...",
                    container=False
                ),
                autofocus=False,
                concurrency_limit=None,  # Allow multiple concurrent chats
                additional_outputs=[sql_input]  # Pass SQL to input box
            )

        # Right panel
        with gr.Column():
            with gr.Accordion("Connection"):
                database = gr.Dropdown(
                    choices=["MySQL", "PostgreSQL", "SQLite", "MSSQL"],
                    label="Database",
                    interactive=True
                )
                url = gr.Textbox(label="URL", value="localhost")
                port = gr.Number(label="Port", value=3306)
                user = gr.Textbox(label="User")
                password = gr.Textbox(label="Password", type="password")
                default_db = gr.Textbox(label="Default Database")
                connect_btn = gr.Button("Connect")

            with gr.Accordion("Models", open=True):
                expert_model = gr.Dropdown(
                    choices=AI_CONFIG.get_model_choices(),
                    label="Expert Model",
                    value=f"{AI_CONFIG.models[0][0]}:{AI_CONFIG.models[0][1]}" if AI_CONFIG.models else None
                )
                reviewer_model = gr.Dropdown(
                    choices=AI_CONFIG.get_model_choices(),
                    label="Reviewer Model",
                    value=(f"{AI_CONFIG.models[1][0]}:{AI_CONFIG.models[1][1]}" if len(AI_CONFIG.models) > 1 
                          else f"{AI_CONFIG.models[0][0]}:{AI_CONFIG.models[0][1]}" if AI_CONFIG.models else None)
                )
            with gr.Accordion("DB Info", open=False):
                output = gr.Textbox(label="Output")
            
            results_df = gr.Dataframe(
                label="Query Results",
                interactive=False,
                wrap=True
            )

    # Initialize models
    init_default_models()
    # Set up event handlers
    database.change(
        fn=update_database_options,
        inputs=database,
        outputs=[database, port]
    )
    
    connect_btn.click(
        fn=connect,
        inputs=[database, url, port, default_db, user, password],
        outputs=output
    )
    
    expert_model.change(
        fn=lambda m, p: on_model_change(m, 'expert', expert_prompt=p),
        inputs=[expert_model, expert_prompt],
        outputs=output
    )
    
    reviewer_model.change(
        fn=lambda m, p: on_model_change(m, 'reviewer', reviewer_prompt=p),
        inputs=[reviewer_model, reviewer_prompt],
        outputs=output
    )

    
    expert_prompt.change(
        fn=lambda p: on_model_change(expert_model.value, 'expert', expert_prompt=p),
        inputs=[expert_prompt],
        outputs=output
    )
    
    reviewer_prompt.change(
        fn=lambda p: on_model_change(reviewer_model.value, 'reviewer', reviewer_prompt=p),
        inputs=[reviewer_prompt],
        outputs=output
    )

    # Add SQL execution handler
    def on_chat_select(evt: gr.SelectData):
        """Handle chat message selection to extract SQL."""
        if evt.value:
            sql_query = AIConfig.extract_sql_query(evt.value["content"])
            if sql_query:
                return sql_query
        return ""

    chat.chatbot.select(
        fn=on_chat_select,
        outputs=sql_input
    )

    execute_btn.click(
        fn=execute_sql,
        inputs=sql_input,
        outputs=results_df,
        api_name="execute_sql"  # Enable async
    )

    # Auto-execute SQL when chat generates it
    async def on_sql_update(sql: str) -> gr.Dataframe:
        """Execute SQL when it's generated from chat."""
        if sql:
            return await execute_sql(sql)
        return gr.Dataframe(value=[])

    sql_input.change(
        fn=on_sql_update,
        inputs=sql_input,
        outputs=results_df,
        api_name="on_sql_update"  # Enable async
    )

if __name__ == "__main__":
    demo.launch(show_error=True, share=False)