from typing import Iterator, Dict, Any, Optional, Union, AsyncIterator, List
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection
from sqlalchemy.engine import Result
from sqlalchemy.sql import text
from contextlib import asynccontextmanager
from dataclasses import dataclass
import time
import asyncio
from concurrent.futures import TimeoutError
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from .query import QueryResult

class AsyncQueryExecutor:
    """Class for executing SQL queries with async support."""
    
    def __init__(self, connection_string: str):
        """Initialize with database connection string."""
        # Convert regular connection string to async version
        if 'postgresql://' in connection_string:
            connection_string = connection_string.replace('postgresql://', 'postgresql+asyncpg://')
        elif 'mysql://' in connection_string:
            connection_string = connection_string.replace('mysql://', 'mysql+aiomysql://')
        elif 'sqlite://' in connection_string:
            connection_string = connection_string.replace('sqlite://', 'sqlite+aiosqlite://')
            
        self.engine: AsyncEngine = create_async_engine(connection_string)
        
    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[AsyncConnection]:
        """Async context manager for database connections."""
        async with self.engine.connect() as connection:
            yield connection
            await connection.commit()
            
    def _create_execution_options(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Create execution options dictionary."""
        options = {}
        if timeout is not None:
            options['timeout'] = timeout
        return options
            
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
        timeout: Optional[float] = None
    ) -> AsyncIterator[tuple[QueryResult, AsyncIterator[Dict[str, Any]]]]:
        """
        Execute a query and return results in chunks asynchronously.
        
        Args:
            query: SQL query to execute
            params: Optional parameters for the query
            chunk_size: Number of rows to fetch at a time
            timeout: Query timeout in seconds (None for no timeout)
            
        Returns:
            AsyncIterator yielding tuples of (QueryResult, row iterator)
        """
        async with self.get_connection() as connection:
            start_time = time.time()
            
            try:
                # Set execution options
                connection = connection.execution_options(**self._create_execution_options(timeout))
                
                # Execute query with timeout if specified
                if timeout is not None:
                    result = await asyncio.wait_for(
                        connection.execute(text(query), params or {}),
                        timeout=timeout
                    )
                else:
                    result = await connection.execute(text(query), params or {})
                
                # Get column information
                columns = result.keys()
                query_result = QueryResult(
                    columns=list(columns),
                    execution_time=time.time() - start_time
                )
                
                async def row_iterator() -> AsyncIterator[Dict[str, Any]]:
                    """Async iterator for fetching rows in chunks."""
                    while True:
                        chunk = await result.fetchmany(chunk_size)
                        if not chunk:
                            break
                        for row in chunk:
                            yield dict(row)
                
                yield query_result, row_iterator()
            except (asyncio.TimeoutError, TimeoutError, SQLAlchemyTimeoutError):
                query_result = QueryResult(
                    columns=[],
                    execution_time=time.time() - start_time,
                    timed_out=True
                )
                async def empty_iterator() -> AsyncIterator[Dict[str, Any]]:
                    if False: yield {}
                yield query_result, empty_iterator()
            
    async def execute_query_with_stats(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """
        Execute a query and return only statistics without fetching results.
        Useful for INSERT, UPDATE, DELETE operations.
        """
        async with self.get_connection() as connection:
            start_time = time.time()
            result = await connection.execute(text(query), params or {})
            execution_time = time.time() - start_time
            
            return QueryResult(
                columns=[],
                row_count=result.rowcount,
                execution_time=execution_time
            )
            
    async def fetch_all(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> tuple[QueryResult, List[Dict[str, Any]]]:
        """
        Execute a query and fetch all results at once asynchronously.
        Warning: This can consume a lot of memory for large result sets.
        """
        async with self.get_connection() as connection:
            start_time = time.time()
            
            # Execute the query
            result = await connection.execute(text(query), params or {})
            rows = [dict(row) for row in result.mappings()]
            columns = list(rows[0].keys()) if rows else []
            
            query_result = QueryResult(
                columns=list(columns),
                row_count=len(rows),
                execution_time=time.time() - start_time
            )
            
            return query_result, rows 