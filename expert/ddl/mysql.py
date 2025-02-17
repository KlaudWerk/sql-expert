"""MySQL DDL generator implementation."""
import sqlalchemy as sa
from typing import List, Dict, Any
from sqlalchemy import inspect
from .base import BaseDDLGenerator

class MySQLDDLGenerator(BaseDDLGenerator):
    """MySQL specific DDL generator."""

    def get_table_ddl(self, table_name: str) -> str:
        """Get DDL for a specific table."""
        table = sa.Table(table_name, self.metadata, autoload_with=self.engine)
        create_table = sa.schema.CreateTable(table)
        return str(create_table.compile(self.engine))

    def get_indexes_ddl(self, table_name: str) -> List[str]:
        """Get DDL for table indexes."""
        indexes = []
        for idx in self.inspector.get_indexes(table_name):
            columns = idx['column_names']
            unique = "UNIQUE " if idx['unique'] else ""
            index_name = idx['name']
            index_type = idx.get('mysql_type', 'BTREE')
            index_ddl = (f"CREATE {unique}INDEX {index_name} ON {table_name} "
                        f"({', '.join(columns)}) USING {index_type};")
            indexes.append(index_ddl)
        return indexes

    def get_foreign_keys_ddl(self, table_name: str) -> List[str]:
        """Get DDL for table foreign keys."""
        foreign_keys = []
        for fk in self.inspector.get_foreign_keys(table_name):
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

    def get_all_tables_ddl(self) -> Dict[str, Any]:
        """Get DDL for all tables in the database."""
        inspector = inspect(self.engine)
        tables = {}
        
        for table_name in inspector.get_table_names():
            table_info = {
                'columns': [],
                'foreign_keys': [],
                'indexes': [],
                'constraints': []
            }
            
            # Get primary key columns first
            pk_columns = set(inspector.get_pk_constraint(table_name)['constrained_columns'])
            
            # Get column information
            for column in inspector.get_columns(table_name):
                col_info = {
                    'name': column['name'],
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'primary_key': column['name'] in pk_columns,  # Use the pk_columns set
                    'default': str(column.get('default', 'None')),
                    'autoincrement': column.get('autoincrement', False)
                }
                table_info['columns'].append(col_info)
            
            # Get foreign key information using reflection
            table = sa.Table(table_name, sa.MetaData(), autoload_with=self.engine)
            for fk in table.foreign_keys:
                fk_info = {
                    'name': fk.name,
                    'constrained_columns': [fk.parent.name],  # Local column
                    'referred_table': fk.column.table.name,   # Referenced table
                    'referred_columns': [fk.column.name],     # Referenced column
                    'options': {
                        'onupdate': fk.onupdate,
                        'ondelete': fk.ondelete
                    }
                }
                table_info['foreign_keys'].append(fk_info)
            
            # Get index information
            for idx in inspector.get_indexes(table_name):
                idx_info = {
                    'name': idx['name'],
                    'columns': idx['column_names'],
                    'unique': idx['unique']
                }
                table_info['indexes'].append(idx_info)
            
            # Get constraint information
            for const in inspector.get_unique_constraints(table_name):
                const_info = {
                    'name': const['name'],
                    'columns': const['column_names']
                }
                table_info['constraints'].append(const_info)
            
            tables[table_name] = table_info
        
        return tables

    def get_complete_ddl(self) -> str:
        """Get complete DDL for the database."""
        tables = self.get_all_tables_ddl()
        ddl_parts = []
        
        for table_name, table_info in tables.items():
            ddl_parts.append(f"-- Table: {table_name}")
            ddl_parts.append("CREATE TABLE IF NOT EXISTS {} (".format(table_name))
            
            # Column definitions
            column_defs = []
            for col in table_info['columns']:
                col_def = f"  {col['name']} {col['type']}"
                if not col['nullable']:
                    col_def += " NOT NULL"
                if col['primary_key']:
                    col_def += " PRIMARY KEY"
                if col['autoincrement']:
                    col_def += " AUTO_INCREMENT"
                if col['default'] != 'None':
                    col_def += f" DEFAULT {col['default']}"
                column_defs.append(col_def)
            
            # Foreign key definitions
            for fk in table_info['foreign_keys']:
                fk_def = f"  FOREIGN KEY ({', '.join(fk['constrained_columns'])}) "
                fk_def += f"REFERENCES {fk['referred_table']} ({', '.join(fk['referred_columns'])})"
                column_defs.append(fk_def)
            
            ddl_parts.append(',\n'.join(column_defs))
            ddl_parts.append(");")
            ddl_parts.append("")  # Empty line for readability
        
        return "\n".join(ddl_parts) 