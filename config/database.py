"""
Database configuration and connection management for SQL Server
"""
import os
import pyodbc
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging

# Load environment variables
load_dotenv()

class DatabaseConfig:
    """Database configuration and connection manager"""
    
    def __init__(self):
        self.server = os.getenv('SQL_SERVER_HOST', 'localhost')
        self.database = os.getenv('SQL_SERVER_DATABASE', 'TimeTracking')
        self.username = os.getenv('SQL_SERVER_USERNAME', '')
        self.password = os.getenv('SQL_SERVER_PASSWORD', '')
        self.driver = '{ODBC Driver 17 for SQL Server}'
        self.connection_string = self._build_connection_string()
        
    def _build_connection_string(self) -> str:
        """Build SQL Server connection string"""
        if self.username and self.password:
            return (f"DRIVER={self.driver};"
                   f"SERVER={self.server};"
                   f"DATABASE={self.database};"
                   f"UID={self.username};"
                   f"PWD={self.password};"
                   f"TrustServerCertificate=yes;")
        else:
            # Integrated authentication
            return (f"DRIVER={self.driver};"
                   f"SERVER={self.server};"
                   f"DATABASE={self.database};"
                   f"Trusted_Connection=yes;"
                   f"TrustServerCertificate=yes;")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with pyodbc.connect(self.connection_string, timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logging.error(f"Database connection test failed: {e}")
            return False
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def execute_query(_self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        try:
            with pyodbc.connect(_self.connection_string) as conn:
                if params:
                    return pd.read_sql(query, conn, params=params)
                else:
                    return pd.read_sql(query, conn)
        except Exception as e:
            logging.error(f"Query execution failed: {e}")
            st.error(f"Database query failed: {str(e)}")
            return pd.DataFrame()
    
    def get_projects(self, user_projects: list) -> pd.DataFrame:
        """Get available projects for user"""
        if not user_projects:
            return pd.DataFrame()
            
        placeholders = ','.join(['?' for _ in user_projects])
        query = f"""
        SELECT DISTINCT [Projekt], [ProjektNr], [Kundenname]
        FROM ZV 
        WHERE [Projekt] IN ({placeholders})
        ORDER BY [Projekt]
        """
        return self.execute_query(query, tuple(user_projects))
    
    def get_time_entries(self, projects: list, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get time entries for specified projects"""
        if not projects:
            return pd.DataFrame()
            
        where_conditions = []
        params = []
        
        # Project filter
        placeholders = ','.join(['?' for _ in projects])
        where_conditions.append(f"[Projekt] IN ({placeholders})")
        params.extend(projects)
        
        # Additional filters
        if filters:
            if filters.get('year'):
                where_conditions.append("[Jahr] = ?")
                params.append(filters['year'])
            if filters.get('month'):
                where_conditions.append("[Monat] = ?")
                params.append(filters['month'])
            if filters.get('status'):
                where_conditions.append("[Status] = ?")
                params.append(filters['status'])
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            [Name],
            [Zeit],
            [Projekt],
            [Teilprojekt],
            [Kostenstelle],
            [Verwendung],
            [Status],
            [Kommentar],
            [Datum],
            [DatumBuchung],
            [Monat],
            [Jahr],
            [VorgangsnummerSage],
            [FaktStd],
            [Kundenname],
            [ProjektleiterName],
            [ProjektNr]
        FROM ZV
        WHERE {where_clause}
        ORDER BY [Projekt], [Verwendung], [Datum] DESC
        """
        
        return self.execute_query(query, tuple(params))
    
    def get_aggregated_data(self, projects: list, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get aggregated time data by activity (Verwendung)"""
        if not projects:
            return pd.DataFrame()
            
        where_conditions = []
        params = []
        
        # Project filter
        placeholders = ','.join(['?' for _ in projects])
        where_conditions.append(f"[Projekt] IN ({placeholders})")
        params.extend(projects)
        
        # Additional filters
        if filters:
            if filters.get('year'):
                where_conditions.append("[Jahr] = ?")
                params.append(filters['year'])
            if filters.get('month'):
                where_conditions.append("[Monat] = ?")
                params.append(filters['month'])
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            [Projekt],
            [ProjektNr],
            [Kundenname],
            [Verwendung] as Activity,
            SUM(CAST([Zeit] as FLOAT)) as ActualHours,
            COUNT(*) as EntryCount,
            MIN([Datum]) as FirstEntry,
            MAX([Datum]) as LastEntry
        FROM ZV
        WHERE {where_clause}
        GROUP BY [Projekt], [ProjektNr], [Kundenname], [Verwendung]
        ORDER BY [Projekt], SUM(CAST([Zeit] as FLOAT)) DESC
        """
        
        return self.execute_query(query, tuple(params))

# Global database instance
db_config = DatabaseConfig()
