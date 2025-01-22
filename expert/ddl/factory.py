from enum import Enum
from typing import Union
from .base import DDLGeneratorProtocol
from .postgresql import PostgreSQLDDLGenerator
from .mysql import MySQLDDLGenerator
from .mssql import MSSQLDDLGenerator

class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MSSQL = "mssql"

def create_ddl_generator(connection_string: str) -> DDLGeneratorProtocol:
    """Factory function to create the appropriate DDL generator."""
    if "postgresql" in connection_string:
        return PostgreSQLDDLGenerator(connection_string)
    elif "mysql" in connection_string:
        return MySQLDDLGenerator(connection_string)
    elif "mssql" in connection_string:
        return MSSQLDDLGenerator(connection_string)
    else:
        raise ValueError("Unsupported database type. Use PostgreSQL, MySQL, or MSSQL.") 