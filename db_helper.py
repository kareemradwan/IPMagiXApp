import pyodbc
import logging
from typing import List, Dict, Any, Tuple, Optional, Union


class SQLServerConnection:
    def __init__(self, connection_string: str):
        """
        Initialize SQL Server connection helper
        
        Args:
            connection_string (str): SQL Server connection string
            Example: "DRIVER={ODBC Driver 17 for SQL Server};SERVER=server_name;DATABASE=db_name;UID=username;PWD=password"
        """
        self.connection_string = connection_string
        self.connection = None
        self.cursor = None
    
    def __enter__(self):
        """
        Context manager entry - opens connection
        """
        self.connection = pyodbc.connect(self.connection_string)
        self.cursor = self.connection.cursor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - closes connection
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def select(self, query: str, params: Optional[Union[Tuple, List, Dict]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as a list of dictionaries
        
        Args:
            query (str): SQL query to execute
            params (Optional[Union[Tuple, List, Dict]]): Parameters to pass to query
            
        Returns:
            List[Dict[str, Any]]: Query results as list of dictionaries (column name: value)
            
        Example:
            results = db.select("SELECT * FROM users WHERE user_id = ?", (123,))
        """
        # Create a fresh connection and cursor for each query to avoid cursor state issues
        with pyodbc.connect(self.connection_string) as connection:
            cursor = connection.cursor()
            try:
                # Execute query with parameters if provided
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Get column names from cursor description
                if not cursor.description:
                    return []
                    
                columns = [column[0] for column in cursor.description]
                
                # Convert rows to list of dictionaries
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
                
            except Exception as e:
                logging.error(f"Error executing SELECT query: {str(e)}")
                logging.error(f"Query: {query}")
                if params:
                    logging.error(f"Parameters: {params}")
                raise
    
    def execute_update(self, query: str, params: Optional[Union[Tuple, List, Dict]] = None) -> int:
        """
        Execute an UPDATE/INSERT/DELETE query and return number of affected rows
        
        Args:
            query (str): SQL query to execute
            params (Optional[Union[Tuple, List, Dict]]): Parameters to pass to query
            
        Returns:
            int: Number of rows affected
            
        Example:
            rows_affected = db.execute_update(
                "UPDATE users SET name = ? WHERE user_id = ?", 
                ("John Doe", 123)
            )
        """
        # Create a fresh connection and cursor for each query to avoid cursor state issues
        with pyodbc.connect(self.connection_string) as connection:
            cursor = connection.cursor()
            try:
                # Execute query with parameters if provided
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Commit changes
                connection.commit()
                
                # Return number of affected rows
                return cursor.rowcount
                
            except Exception as e:
                connection.rollback()
                logging.error(f"Error executing UPDATE query: {str(e)}")
                logging.error(f"Query: {query}")
                if params:
                    logging.error(f"Parameters: {params}")
                raise


# Example usage
def get_connection(conn_string: str) -> SQLServerConnection:
    """
    Create and return a SQL Server connection object
    
    Args:
        conn_string (str): Connection string for SQL Server
        
    Returns:
        SQLServerConnection: Connection helper object
    """
    return SQLServerConnection(conn_string)


# Example usage with context manager
"""
# Usage example:

# Connection string
conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=myserver;DATABASE=mydatabase;UID=myusername;PWD=mypassword"

# Using context manager (recommended)
with get_connection(conn_str) as db:
    # Select example
    users = db.select("SELECT * FROM users WHERE dept_id = ?", (5,))
    for user in users:
        print(f"User: {user['username']}, Email: {user['email']}")
    
    # Update example
    affected_rows = db.execute_update(
        "UPDATE products SET price = ? WHERE product_id = ?", 
        (19.99, 1001)
    )
    print(f"Updated {affected_rows} rows")

# Direct usage (make sure to close connection manually)
db_conn = get_connection(conn_str)
try:
    products = db_conn.select("SELECT * FROM products WHERE price < ?", (100,))
    print(f"Found {len(products)} products")
finally:
    # Close connections
    if db_conn.cursor:
        db_conn.cursor.close()
    if db_conn.connection:
        db_conn.connection.close()
"""





# Singleton Connection Manager
class DBConnectionManager:
    _instance = None
    _connection_string = None
    
    @classmethod
    def initialize(cls, connection_string):
        """
        Initialize the database connection manager with a connection string.
        Must be called once before get_instance().
        
        Args:
            connection_string (str): SQL Server connection string
        """
        cls._connection_string = connection_string
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of the connection manager.
        Will create a new instance if one doesn't exist.
        
        Returns:
            DBConnectionManager: Singleton instance
            
        Raises:
            RuntimeError: If initialize() wasn't called first
        """
        if cls._connection_string is None:
            raise RuntimeError("DBConnectionManager.initialize() must be called before get_instance()")
            
        if cls._instance is None:
            cls._instance = cls()
            
        return cls._instance
    
    def get_connection_string(self):
        """
        Get the database connection string.
        
        Returns:
            str: Database connection string
        """
        return self._connection_string
    
    def get_connection(self):
        """
        Get a fresh database connection.
        
        Returns:
            SQLServerConnection: Database connection object
        """
        return SQLServerConnection(self._connection_string)
    
    def select(self, query, params=None):
        """
        Execute a SELECT query using the singleton connection.
        
        Args:
            query (str): SQL query to execute
            params: Parameters to pass to query
            
        Returns:
            List[Dict]: Query results
        """
        conn = self.get_connection()
        return conn.select(query, params)
    
    def execute_update(self, query, params=None):
        """
        Execute an UPDATE/INSERT/DELETE query using the singleton connection.
        
        Args:
            query (str): SQL query to execute
            params: Parameters to pass to query
            
        Returns:
            int: Number of rows affected
        """
        conn = self.get_connection()
        return conn.execute_update(query, params)
    
    def close(self):
        """
        No longer needed as we're using fresh connections for each query.
        Kept for backward compatibility.
        """
        pass

