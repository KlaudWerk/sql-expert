from typing import List, Dict, Any, Optional, Protocol
import sqlalchemy as sa
from sqlalchemy import inspect, MetaData
from abc import ABC, abstractmethod
from enum import Enum

class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MSSQL = "mssql"

class DDLGeneratorProtocol(Protocol):
    """Protocol defining the interface for DDL generation."""
    def get_table_ddl(self, table_name: str) -> str: ...
    def get_indexes_ddl(self, table_name: str) -> List[str]: ...
    def get_foreign_keys_ddl(self, table_name: str) -> List[str]: ...
    def get_complete_ddl(self) -> str: ...
    def get_all_tables_ddl(self) -> Dict[str, str]: ...

class BaseDDLGenerator(ABC):
    """Base class implementing common DDL generation functionality."""
    def __init__(self, connection_string: str):
        self.engine = sa.create_engine(connection_string)
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()

    def get_schema_name(self, table_name: str) -> Optional[str]:
        if '.' in table_name:
            return table_name.split('.')[0]
        return None

    def get_all_tables_ddl(self) -> Dict[str, str]:
        table_ddls = {}
        for table_name in self.inspector.get_table_names():
            table_ddls[table_name] = self.get_table_ddl(table_name)
        return table_ddls

    @abstractmethod
    def get_table_ddl(self, table_name: str) -> str:
        pass

    @abstractmethod
    def get_indexes_ddl(self, table_name: str) -> List[str]:
        pass

    @abstractmethod
    def get_foreign_keys_ddl(self, table_name: str) -> List[str]:
        pass

    @abstractmethod
    def get_complete_ddl(self) -> str:
        pass

class PostgreSQLDDLGenerator(BaseDDLGenerator):
    """PostgreSQL-specific DDL generator."""
    def get_table_ddl(self, table_name: str) -> str:
        table = sa.Table(table_name, self.metadata, autoload_with=self.engine)
        return str(sa.schema.CreateTable(table).compile(self.engine))

    def get_indexes_ddl(self, table_name: str) -> List[str]:
        indexes = []
        schema = self.get_schema_name(table_name)
        
        for index in self.inspector.get_indexes(table_name, schema=schema):
            columns = index['column_names']
            unique = "UNIQUE " if index['unique'] else ""
            index_name = index['name']
            index_ddl = f"CREATE {unique}INDEX {index_name} ON {table_name} ({', '.join(columns)});"
            indexes.append(index_ddl)
        return indexes

    def get_foreign_keys_ddl(self, table_name: str) -> List[str]:
        foreign_keys = []
        schema = self.get_schema_name(table_name)
        
        for fk in self.inspector.get_foreign_keys(table_name, schema=schema):
            constrained_cols = fk['constrained_columns']
            referred_cols = fk['referred_columns']
            referred_table = fk['referred_table']
            fk_name = fk['name']
            
            fk_ddl = (f"ALTER TABLE {table_name} ADD CONSTRAINT {fk_name} "
                     f"FOREIGN KEY ({', '.join(constrained_cols)}) "
                     f"REFERENCES {referred_table} ({', '.join(referred_cols)});")
            foreign_keys.append(fk_ddl)
        return foreign_keys

    def get_complete_ddl(self) -> str:
        ddl_parts = []
        
        for table_name in self.inspector.get_table_names():
            ddl_parts.append(self.get_table_ddl(table_name))
            ddl_parts.append("\n")
            
            indexes = self.get_indexes_ddl(table_name)
            if indexes:
                ddl_parts.extend(indexes)
                ddl_parts.append("\n")
            
            foreign_keys = self.get_foreign_keys_ddl(table_name)
            if foreign_keys:
                ddl_parts.extend(foreign_keys)
                ddl_parts.append("\n")
        
        return "\n".join(ddl_parts)

class MySQLDDLGenerator(BaseDDLGenerator):
    """MySQL-specific DDL generator."""
    def get_table_ddl(self, table_name: str) -> str:
        table = sa.Table(table_name, self.metadata, autoload_with=self.engine)
        create_table = sa.schema.CreateTable(table)
        
        table_options = []
        table_info = self.inspector.get_table_options(table_name)
        if table_info:
            if 'mysql_engine' in table_info:
                table_options.append(f"ENGINE={table_info['mysql_engine']}")
            if 'mysql_charset' in table_info:
                table_options.append(f"CHARACTER SET {table_info['mysql_charset']}")
            if 'mysql_collate' in table_info:
                table_options.append(f"COLLATE {table_info['mysql_collate']}")
        
        ddl = str(create_table.compile(self.engine))
        if table_options:
            ddl = f"{ddl} {' '.join(table_options)}"
        return ddl

    def get_indexes_ddl(self, table_name: str) -> List[str]:
        indexes = []
        schema = self.get_schema_name(table_name)
        
        for index in self.inspector.get_indexes(table_name, schema=schema):
            columns = index['column_names']
            unique = "UNIQUE " if index['unique'] else ""
            index_name = index['name']
            index_type = index.get('mysql_type', 'BTREE')
            index_ddl = (f"CREATE {unique}INDEX {index_name} ON {table_name} "
                        f"({', '.join(columns)}) USING {index_type};")
            indexes.append(index_ddl)
        return indexes

    def get_foreign_keys_ddl(self, table_name: str) -> List[str]:
        foreign_keys = []
        schema = self.get_schema_name(table_name)
        
        for fk in self.inspector.get_foreign_keys(table_name, schema=schema):
            constrained_cols = fk['constrained_columns']
            referred_cols = fk['referred_columns']
            referred_table = fk['referred_table']
            fk_name = fk['name']
            
            options = []
            if 'onupdate' in fk:
                options.append(f"ON UPDATE {fk['onupdate']}")
            if 'ondelete' in fk:
                options.append(f"ON DELETE {fk['ondelete']}")
            
            fk_ddl = (f"ALTER TABLE {table_name} ADD CONSTRAINT {fk_name} "
                     f"FOREIGN KEY ({', '.join(constrained_cols)}) "
                     f"REFERENCES {referred_table} ({', '.join(referred_cols)}) "
                     f"{' '.join(options)};")
            foreign_keys.append(fk_ddl)
        return foreign_keys

    def get_complete_ddl(self) -> str:
        ddl_parts = ["SET FOREIGN_KEY_CHECKS=0;\n"]
        
        for table_name in self.inspector.get_table_names():
            ddl_parts.append(self.get_table_ddl(table_name))
            ddl_parts.append("\n")
            
            indexes = self.get_indexes_ddl(table_name)
            if indexes:
                ddl_parts.extend(indexes)
                ddl_parts.append("\n")
            
            foreign_keys = self.get_foreign_keys_ddl(table_name)
            if foreign_keys:
                ddl_parts.extend(foreign_keys)
                ddl_parts.append("\n")
        
        ddl_parts.append("SET FOREIGN_KEY_CHECKS=1;\n")
        return "\n".join(ddl_parts)

class MSSQLDDLGenerator(BaseDDLGenerator):
    """MS SQL Server-specific DDL generator."""
    def get_table_ddl(self, table_name: str) -> str:
        table = sa.Table(table_name, self.metadata, autoload_with=self.engine)
        return str(sa.schema.CreateTable(table).compile(self.engine))

    def get_indexes_ddl(self, table_name: str) -> List[str]:
        indexes = []
        schema = self.get_schema_name(table_name)
        
        for index in self.inspector.get_indexes(table_name, schema=schema):
            columns = index['column_names']
            unique = "UNIQUE " if index['unique'] else ""
            index_name = index['name']
            index_ddl = (f"CREATE {unique}INDEX {index_name} ON {table_name} "
                        f"({', '.join(columns)}) WITH (ONLINE = ON);")
            indexes.append(index_ddl)
        return indexes

    def get_foreign_keys_ddl(self, table_name: str) -> List[str]:
        foreign_keys = []
        schema = self.get_schema_name(table_name)
        
        for fk in self.inspector.get_foreign_keys(table_name, schema=schema):
            constrained_cols = fk['constrained_columns']
            referred_cols = fk['referred_columns']
            referred_table = fk['referred_table']
            fk_name = fk['name']
            
            fk_ddl = (f"ALTER TABLE {table_name} ADD CONSTRAINT {fk_name} "
                     f"FOREIGN KEY ({', '.join(constrained_cols)}) "
                     f"REFERENCES {referred_table} ({', '.join(referred_cols)});")
            foreign_keys.append(fk_ddl)
        return foreign_keys

    def get_complete_ddl(self) -> str:
        ddl_parts = ["SET NOCOUNT ON;\n"]
        
        for table_name in self.inspector.get_table_names():
            ddl_parts.append(self.get_table_ddl(table_name))
            ddl_parts.append("\n")
            
            indexes = self.get_indexes_ddl(table_name)
            if indexes:
                ddl_parts.extend(indexes)
                ddl_parts.append("\n")
            
            foreign_keys = self.get_foreign_keys_ddl(table_name)
            if foreign_keys:
                ddl_parts.extend(foreign_keys)
                ddl_parts.append("\n")
        
        return "\n".join(ddl_parts)

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