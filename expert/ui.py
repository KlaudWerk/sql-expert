import gradio as gr
from gradio import ChatMessage
from expert.tool.connection import DatabaseConnection
from expert.ddl import DatabaseType
from expert.ai.config import AIConfig
from typing import Dict, List, Tuple, Optional, AsyncGenerator, TypedDict, Union
from expert.ai.protocol import AIMessageDict
from expert.ai.default_sys_prompts import DEFAULT_USER_REVIEWER_PROMPT
from expert.utils.logger import setup_logger, logger
from dotenv import load_dotenv
import traceback
import json


# Load environment variables
load_dotenv()

# Setup logger
setup_logger()

# Initialize global instances
DB = DatabaseConnection()
AI_CONFIG = AIConfig()

# Initialize default AI models
def init_default_models():
    """Initialize AI models with defaults from environment."""
    try:
        # Set expert to first available model
        if AI_CONFIG.expert_models:
            provider, model = AI_CONFIG.expert_models[0]
            logger.info(f"Initializing expert model: {provider}:{model}")
            AI_CONFIG.create_ai(model_str=f"{provider}:{model}", role='expert')
            

        # Set reviewer to second available model, or first if only one exists
        if AI_CONFIG.reviewer_models:
            provider, model = AI_CONFIG.reviewer_models[0]
            logger.info(f"Initializing reviewer model: {provider}:{model}")
            AI_CONFIG.create_ai(model_str=f"{provider}:{model}", role='reviewer')
            
        return True
    except Exception as e:
        logger.error(f"Error initializing default models: {str(e)}")

        traceback.print_exc()
        return False
 

async def execute_sql(query: str) -> gr.Dataframe:
    """Execute SQL query and return formatted results."""
    if not DB.is_connected:
        return gr.Dataframe(value=[])
        
    try:
        logger.info(f"Executing SQL query: {query}")
        query_result, rows = await DB.async_executor.fetch_all(query)
        
        if rows:
            headers = list(rows[0].keys())
            data = [[str(row[h]) for h in headers] for row in rows]
            return gr.Dataframe(value=data, headers=headers)
        
        return gr.Dataframe(value=[])
    except Exception as e:
        logger.error(f"SQL execution failed: {str(e)}")
        traceback.print_exc()
        return gr.Dataframe(value=[])

async def ask_question(message: str, history: List[ChatMessage]) -> AsyncGenerator[List[Tuple[ChatMessage,str]], None]:
    """
    Handle chat messages and yield only the latest chat response, not the entire conversation history.
    
    Note: Gradio's ChatInterface may supply the history as dictionaries rather than ChatMessage objects.
    """
    # Early exit if AI models are not set up.
    while not AI_CONFIG.expert or not AI_CONFIG.reviewer:
        yield ChatMessage(role="assistant", content="Please select both Expert and Reviewer models first."), ""

    try:
        # Helper function to extract role and content regardless of the message type.
        def get_role_content(msg: Union[Dict[str, str], ChatMessage]) -> Tuple[str, str]:
            """
            Args:
                msg: A dictionary with 'role' and 'content' keys or a ChatMessage object.
            Returns:
                A tuple: (role, content)
            """
            if isinstance(msg, dict):
                return msg["role"], msg["content"]
            return msg.role, msg.content

        # Convert chat history to the format expected by the AI expert (i.e. AIMessageDict).
        ai_history = [
            AIMessageDict(role=get_role_content(msg)[0], content=get_role_content(msg)[1])
            for msg in history if get_role_content(msg)[0] in ["user", "assistant"]
        ]

        expert_chunks = []
        last_yielded = ""
        # Stream expert response chunks.
        async for chunk in AI_CONFIG.expert.stream(message, ai_history):
            expert_chunks.append(chunk)
            complete_response = ''.join(expert_chunks)
            # Only yield (as the sole new message) when the complete_response ends with punctuation
            # (signaling a likely natural break).
            if complete_response != last_yielded:
                if any(complete_response.endswith(end) for end in ['.', '!', '?', ':', '\n']):
                    last_yielded = complete_response
                    chat_msg = ChatMessage(role="assistant", content=complete_response)
                    history.append(chat_msg)
                    yield chat_msg, ""
        


        # Ensure that the final expert response is yielded if not already done.
        complete_response = ''.join(expert_chunks)
        if complete_response != last_yielded:

            chat_msg = ChatMessage(role="assistant", content=complete_response)
            history.append(chat_msg)
            print("--- yeld --- ")
            yield chat_msg, ""


    except Exception as e:
        logger.error(f"Error in ask_question: {str(e)}")
        traceback.print_exc()
        yield ChatMessage(role="assistant", content=f"Error: {str(e)}"), ""


def connect(database: str, url: str, port: str, default_db: str, user: str, password: str) -> Tuple[str, str]:
    """Handle database connection."""
    logger.info(f"Connecting to {database} at {url}:{port} default db [{default_db}] with user [{user}]")
    
    try:
        if DB.is_connected:
            DB.disconnect()
            
        # Convert database type using match statement
        match database:
            case "MySQL":
                db_type = DatabaseType.MYSQL.value
                default_db = default_db or "mydb"
            case "PostgreSQL":
                db_type = DatabaseType.POSTGRESQL.value
                default_db = default_db or "postgres"
            case "SQLite":
                db_type = DatabaseType.SQLITE.value
                default_db = default_db or "sqlite"
            case "MSSQL":
                db_type = DatabaseType.MSSQL.value
                default_db = default_db or "mssql"
            case _:
                raise ValueError(f"Unsupported database type: {database}")

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
        
        gr.Info(f"Successfully connected to {database} at {url}:{port}")
        status = f"Connected to {database} at {url}:{port}"
        details = f"Connected to {database} at {url}:{port} with user {user}\nDDL:\n{DB.db_info.ddl}"
        return status, details
        
    except Exception as e:
        gr.Warning(f"Connection failed: {str(e)}")
        error_msg = f"Connection failed: {str(e)}"
        return error_msg, error_msg

def update_database_options(database: str) -> Tuple[str, int]:
    """Update database-specific options."""
    logger.debug(f"Updating database options for {database}")
    match database:
        case "MySQL":
            return "MySQL", 3306
        case "PostgreSQL":
            return "PostgreSQL", 5432
        case "SQLite":
            return "SQLite", 5432
        case "MSSQL":
            return "MSSQL", 1433
        case _:
            return "MySQL", 3306  # Default case

def on_model_change(
    model: str,
    role: str,
    expert_prompt: Optional[str] = None,
    reviewer_prompt: Optional[str] = None
) -> str:
    """Handle model selection change."""
    try:
        logger.info(f"Setting up {role} model: {model}")
        logger.debug(f"Expert prompt: {expert_prompt}")
        logger.debug(f"Reviewer prompt: {reviewer_prompt}")
        
        prompt = expert_prompt if role == 'expert' else reviewer_prompt
        AI_CONFIG.create_ai(model, role, system_prompt=prompt)
        if DB.is_connected:
            if role == 'expert':
                AI_CONFIG.expert.init(DB.get_ddl())
            else:
                AI_CONFIG.reviewer.init(DB.get_ddl())
        return f"Selected {role} model: {model}"
    except Exception as e:
        logger.error(f"Error setting up model: {str(e)}")
        traceback.print_exc()
        return f"Error setting up model: {str(e)}"

# Create Gradio interface
with gr.Blocks() as demo:
    with gr.Row():
        # Left panel
        with gr.Column():
            connection_status = gr.Markdown(
                value="Not connected to database",
                label="Connection Status"
            )
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
            with gr.Blocks() as chatbot:
                chat_bot = gr.Chatbot(
                    height=300,
                    type="messages",
                    show_label=False,
                    render_markdown=True,
                    bubble_full_width=False
                )
                msg = gr.Textbox(
                    placeholder="Ask me about the database...",
                    container=False
                )
                clear = gr.Button("Clear")


            chat = gr.ChatInterface(
                ask_question,
                type="messages",
                chatbot=gr.Chatbot(
                    height=300,
                    type="messages",
                    show_label=False,
                    render_markdown=True,
                    bubble_full_width=False
                ),
                textbox=gr.Textbox(
                    placeholder="Ask me about the database...",
                    container=False
                ),
                autofocus=False,
                concurrency_limit=None,  # Allow multiple concurrent chats
                additional_outputs=[sql_input],  # Pass SQL to input box
                api_name="ask_question"  # Enable async
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
                    choices=AI_CONFIG.get_expert_model_choices(),
                    label="Expert Model",
                    value=f"{AI_CONFIG.expert_models[0][0]}:{AI_CONFIG.expert_models[0][1]}" if AI_CONFIG.expert_models else None
                )

                reviewer_model = gr.Dropdown(
                    choices=AI_CONFIG.get_reviewer_model_choices(),
                    label="Reviewer Model",
                    value=(f"{AI_CONFIG.reviewer_models[0][0]}:{AI_CONFIG.reviewer_models[0][1]}" if len(AI_CONFIG.reviewer_models) > 1 
                           else f"{AI_CONFIG.reviewer_models[0][0]}:{AI_CONFIG.reviewer_models[0][1]}" if AI_CONFIG.reviewer_models else None)
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
        outputs=[connection_status, output]
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