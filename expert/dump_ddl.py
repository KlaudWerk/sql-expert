#!/usr/bin/env python3
import argparse
import sys
from typing import Optional
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os
from rich import print as rprint
from .ddl import create_ddl_generator, DatabaseType

# Load environment variables
load_dotenv()

def create_connection_string(
    db_type: str,
    host: str,
    database: str,
    username: str,
    password: str,
    port: Optional[int] = None
) -> str:
    """Create a database connection string based on the database type and credentials."""
    # URL encode the password to handle special characters
    encoded_password = quote_plus(password)
    
    if db_type == DatabaseType.POSTGRESQL.value:
        port = port or 5432
        return f"postgresql://{username}:{encoded_password}@{host}:{port}/{database}"
    
    elif db_type == DatabaseType.MYSQL.value:
        port = port or 3306
        return f"mysql://{username}:{encoded_password}@{host}:{port}/{database}"
    
    elif db_type == DatabaseType.MSSQL.value:
        port = port or 1433
        return (f"mssql+pyodbc://{username}:{encoded_password}@{host}:{port}/{database}"
                "?driver=ODBC+Driver+17+for+SQL+Server")
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate DDL statements from a database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dump PostgreSQL DDL
  ./dump_ddl.py postgresql --host localhost --database mydb --username myuser --password mypass

  # Dump MySQL DDL with custom port
  ./dump_ddl.py mysql --host db.example.com --port 3307 --database mydb --username myuser --password mypass

  # Dump MSSQL DDL
  ./dump_ddl.py mssql --host sqlserver --database mydb --username sa --password MyPass123
        """
    )

    parser.add_argument(
        "--db-type",
        choices=[db_type.value for db_type in DatabaseType],
        help="Database type (postgresql, mysql, or mssql)"
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
        help="Database port (default: from DB_PORT env var or PostgreSQL=5432, MySQL=3306, MSSQL=1433)"
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
        "--output",
        help="Output file (default: stdout)"
    )

    return parser

def main():
    """Main function to handle DDL dump."""
    parser = setup_argument_parser()
    args = parser.parse_args()

    try:
        # Create connection string
        connection_string = create_connection_string(
            db_type=args.db_type,
            host=args.host,
            port=args.port,
            database=args.database,
            username=args.username,
            password=args.password
        )

        # Create DDL generator
        generator = create_ddl_generator(connection_string)
        
        # Generate DDL
        ddl = generator.get_complete_ddl()

        # Output DDL
        if args.output:
            with open(args.output, 'w') as f:
                f.write(ddl)
            print(f"DDL has been written to {args.output}")
        else:
            print(ddl)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 