from typing import Optional, Dict, Any
from dataclasses import dataclass
from functools import lru_cache
import sqlalchemy as sa
from sqlalchemy.engine import Engine
from ..ddl import create_ddl_generator, DatabaseType
from .query import QueryExecutor
from .async_query import AsyncQueryExecutor

@dataclass
class DatabaseInfo:
    """Class to hold database connection and metadata information."""
    host: str
    port: int
    database: str
    username: str
    password: str
    db_type: DatabaseType
    connection_string: str
    ddl: Optional[str] = None
    tables: Dict[str, Any] = None

    def __str__(self) -> str:
        """Override string representation to hide password."""
        return f"DatabaseInfo(host={self.host}, port={self.port}, database={self.database}, username={self.username}, db_type={self.db_type})"

    def __repr__(self) -> str:
        """Override repr to hide password."""
        return self.__str__()

class DatabaseConnection:
    """Singleton class to manage database connections and metadata."""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._db_info: Optional[DatabaseInfo] = None
            self._sync_executor: Optional[QueryExecutor] = None
            self._async_executor: Optional[AsyncQueryExecutor] = None
            self._engine: Optional[Engine] = None
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._db_info is not None
    
    @property
    def db_info(self) -> Optional[DatabaseInfo]:
        """Get current database information."""
        return self._db_info
    
    @property
    def sync_executor(self) -> Optional[QueryExecutor]:
        """Get synchronous query executor."""
        return self._sync_executor
    
    @property
    def async_executor(self) -> Optional[AsyncQueryExecutor]:
        """Get asynchronous query executor."""
        return self._async_executor
    
    def _create_connection_string(
        self,
        db_type: str,
        host: str,
        database: str,
        username: str,
        password: str,
        port: Optional[int] = None
    ) -> str:
        """Create database connection string."""
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
    
    def connect(
        self,
        db_type: str,
        host: str,
        database: str,
        username: str,
        password: str,
        port: Optional[int] = None
    ) -> None:
        """
        Connect to database and extract DDL information.
        
        Args:
            db_type: Type of database (postgresql, mysql, mssql)
            host: Database host
            database: Database name
            username: Database username
            password: Database password
            port: Database port (optional)
        """
        # Create connection string
        connection_string = self._create_connection_string(
            db_type=db_type,
            host=host,
            database=database,
            username=username,
            password=password,
            port=port
        )
        
        # Create engine and test connection
        self._engine = sa.create_engine(connection_string)
        self._engine.connect()  # Test connection
        
        # Create executors
        self._sync_executor = QueryExecutor(connection_string)
        self._async_executor = AsyncQueryExecutor(connection_string)
        
        # Create DDL generator and extract DDL
        ddl_generator = create_ddl_generator(connection_string)
        ddl = ddl_generator.get_complete_ddl()
        tables = ddl_generator.get_all_tables_ddl()
        
        # Store database information
        self._db_info = DatabaseInfo(
            host=host,
            port=port or self._get_default_port(db_type),
            database=database,
            username=username,
            password=password,
            db_type=DatabaseType(db_type),
            connection_string=connection_string,
            ddl=ddl,
            tables=tables
        )
    
    def disconnect(self) -> None:
        """Disconnect from database and clean up resources."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
        
        self._sync_executor = None
        self._async_executor = None
        self._db_info = None
        self._initialized = False
    
    def _get_default_port(self, db_type: str) -> int:
        """Get default port for database type."""
        if db_type == DatabaseType.POSTGRESQL.value:
            return 5432
        elif db_type == DatabaseType.MYSQL.value:
            return 3306
        elif db_type == DatabaseType.MSSQL.value:
            return 1433
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    @lru_cache(maxsize=1)
    def get_ddl(self) -> Optional[str]:
        """Get cached DDL for current database."""
        return self._db_info.ddl if self._db_info else None
    
    @lru_cache(maxsize=1)
    def get_tables(self) -> Optional[Dict[str, Any]]:
        """Get cached table DDL information."""
        return self._db_info.tables if self._db_info else None 