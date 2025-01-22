from typing import List, Dict, Any, Optional, Protocol
import sqlalchemy as sa
from sqlalchemy import inspect, MetaData
from abc import ABC, abstractmethod

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