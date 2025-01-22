#!/usr/bin/env python3
import argparse
import sys
import asyncio
from typing import Optional
from dotenv import load_dotenv
import os
from rich import print as rprint
from rich.table import Table
from rich.console import Console
from .tool.async_query import AsyncQueryExecutor
from .ddl import DatabaseType
from .run_query import setup_argument_parser, create_connection_string, display_results

async def main():
    """Main function to handle async query execution."""
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

        # Execute query asynchronously
        executor = AsyncQueryExecutor(connection_string)
        query_result, rows = await executor.fetch_all(query, timeout=args.timeout)

        # Display results
        display_results(query_result, rows)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 