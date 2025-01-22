import sqlalchemy as sa
from typing import List, Dict
from .base import BaseDDLGenerator

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