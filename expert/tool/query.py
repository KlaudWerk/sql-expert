from typing import Iterator, Dict, Any, Optional, Union
import sqlalchemy as sa
from sqlalchemy.engine import Engine, Connection, Result
from sqlalchemy.sql import text
from contextlib import contextmanager
from dataclasses import dataclass
import time
from concurrent.futures import TimeoutError
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError

@dataclass
class QueryResult:
    """Class to hold query execution results and metadata."""
    columns: list[str]
    row_count: Optional[int] = None
    execution_time: Optional[float] = None
    timed_out: bool = False
    
    def __str__(self) -> str:
        parts = []
        if self.row_count is not None:
            parts.append(f"Row count: {self.row_count}")
        if self.execution_time is not None:
            parts.append(f"Execution time: {self.execution_time:.2f}s")
        if self.timed_out:
            parts.append("Query timed out")
        return ", ".join(parts)

class QueryExecutor:
    """Class for executing SQL queries with streaming support."""
    
    def __init__(self, connection_string: str):
        """Initialize with database connection string."""
        self.engine = sa.create_engine(connection_string)
        
    @contextmanager
    def get_connection(self) -> Iterator[Connection]:
        """Context manager for database connections."""
        with self.engine.connect() as connection:
            yield connection
            
    def _create_execution_options(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Create execution options dictionary."""
        options = {}
        if timeout is not None:
            options['timeout'] = timeout
        return options
            
    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
        timeout: Optional[float] = None
    ) -> Iterator[tuple[QueryResult, Iterator[Dict[str, Any]]]]:
        """
        Execute a query and return results in chunks.
        
        Args:
            query: SQL query to execute
            params: Optional parameters for the query
            chunk_size: Number of rows to fetch at a time
            timeout: Query timeout in seconds (None for no timeout)
            
        Returns:
            Iterator yielding tuples of (QueryResult, row iterator)
        """
        with self.get_connection() as connection:
            start_time = time.time()
            
            try:
                # Set execution options
                connection = connection.execution_options(**self._create_execution_options(timeout))
                
                # Execute the query
                result: Result = connection.execute(text(query), params or {})
                
                # Get column information
                columns = result.keys()
                query_result = QueryResult(
                    columns=list(columns),
                    execution_time=time.time() - start_time
                )
                
                def row_iterator() -> Iterator[Dict[str, Any]]:
                    """Iterator for fetching rows in chunks."""
                    while True:
                        chunk = result.fetchmany(chunk_size)
                        if not chunk:
                            break
                        for row in chunk:
                            yield dict(row)
                
                yield query_result, row_iterator()
            except (TimeoutError, SQLAlchemyTimeoutError):
                query_result = QueryResult(
                    columns=[],
                    execution_time=time.time() - start_time,
                    timed_out=True
                )
                yield query_result, iter([])
            
    def execute_query_with_stats(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """
        Execute a query and return only statistics without fetching results.
        Useful for INSERT, UPDATE, DELETE operations.
        
        Args:
            query: SQL query to execute
            params: Optional parameters for the query
            
        Returns:
            QueryResult with execution statistics
        """
        import time
        
        with self.get_connection() as connection:
            start_time = time.time()
            result = connection.execute(text(query), params or {})
            execution_time = time.time() - start_time
            
            return QueryResult(
                columns=[],
                row_count=result.rowcount,
                execution_time=execution_time
            )
            
    def fetch_all(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> tuple[QueryResult, list[Dict[str, Any]]]:
        """
        Execute a query and fetch all results at once.
        Warning: This can consume a lot of memory for large result sets.
        
        Args:
            query: SQL query to execute
            params: Optional parameters for the query
            
        Returns:
            Tuple of (QueryResult, list of rows)
        """
        query_result, row_iterator = next(self.execute_query(query, params))
        rows = list(row_iterator)
        query_result.row_count = len(rows)
        return query_result, rows 