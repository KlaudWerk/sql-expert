#!/usr/bin/env python3
import argparse
import sys
from typing import Optional
from dotenv import load_dotenv
import os
from rich import print as rprint
from rich.table import Table
from rich.console import Console
from .tool.query import QueryExecutor
from .ddl import DatabaseType

def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Execute SQL query and display results",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--db-type",
        choices=[db_type.value for db_type in DatabaseType],
        default=os.getenv("DB_TYPE"),
        help="Database type (default: from DB_TYPE env var)"
    )
    
    parser.add_argument(
        "--host",
        default=os.getenv("DB_HOST"),
        help="Database host (default: from DB_HOST env var)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=os.getenv("DB_PORT"),
        help="Database port (default: from DB_PORT env var)"
    )
    
    parser.add_argument(
        "--database",
        default=os.getenv("DB_NAME"),
        help="Database name (default: from DB_NAME env var)"
    )
    
    parser.add_argument(
        "--username",
        default=os.getenv("DB_USER"),
        help="Database username (default: from DB_USER env var)"
    )
    
    parser.add_argument(
        "--password",
        default=os.getenv("DB_PASSWORD"),
        help="Database password (default: from DB_PASSWORD env var)"
    )

    parser.add_argument(
        "--query",
        help="SQL query to execute"
    )

    parser.add_argument(
        "--file",
        help="File containing SQL query"
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Number of rows to fetch at a time (default: 1000)"
    )

    parser.add_argument(
        "--timeout",
        type=float,
        help="Query timeout in seconds"
    )

    return parser

def create_connection_string(
    db_type: str,
    host: str,
    database: str,
    username: str,
    password: str,
    port: Optional[int] = None
) -> str:
    """Create connection string based on database type and credentials."""
    if db_type == DatabaseType.POSTGRESQL.value:
        port = port or 5432
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    elif db_type == DatabaseType.MYSQL.value:
        port = port or 3306
        return f"mysql://{username}:{password}@{host}:{port}/{database}"
    elif db_type == DatabaseType.MSSQL.value:
        port = port or 1433
        return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def display_results(query_result: QueryResult, rows: list[Dict[str, Any]]):
    """Display query results in a formatted table."""
    console = Console()
    
    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    
    # Add columns
    for column in query_result.columns:
        table.add_column(column)
    
    # Add rows
    for row in rows:
        table.add_row(*[str(row[column]) for column in query_result.columns])
    
    # Print table and statistics
    console.print(table)
    console.print(f"\n[bold green]{str(query_result)}[/bold green]")

def main():
    """Main function to handle query execution."""
    load_dotenv()
    parser = setup_argument_parser()
    args = parser.parse_args()

    try:
        # Get query from file or command line
        if args.file:
            with open(args.file, 'r') as f:
                query = f.read()
        elif args.query:
            query = args.query
        else:
            parser.error("Either --query or --file must be provided")

        # Create connection string
        connection_string = create_connection_string(
            db_type=args.db_type,
            host=args.host,
            port=args.port,
            database=args.database,
            username=args.username,
            password=args.password
        )

        # Execute query
        executor = QueryExecutor(connection_string)
        query_result, rows = executor.fetch_all(query)

        # Display results
        display_results(query_result, rows)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 