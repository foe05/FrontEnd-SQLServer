"""
Database configuration and connection management for SQL Server
"""
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging
import warnings

# Import database drivers
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    logging.warning("pyodbc not available - using fallback mode")

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import URL
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logging.warning("sqlalchemy not available - using pyodbc fallback")

# Suppress pandas SQLAlchemy warning when using pyodbc
warnings.filterwarnings('ignore', message='pandas only supports SQLAlchemy')

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
        self.engine = self._create_engine() if SQLALCHEMY_AVAILABLE else None
        
    def _build_connection_string(self) -> str:
        """Build SQL Server connection string (for pyodbc)"""
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
    
    def _create_engine(self):
        """Create SQLAlchemy engine for pandas compatibility"""
        if not SQLALCHEMY_AVAILABLE:
            return None
        
        try:
            if self.username and self.password:
                connection_url = URL.create(
                    "mssql+pyodbc",
                    username=self.username,
                    password=self.password,
                    host=self.server,
                    database=self.database,
                    query={
                        "driver": "ODBC Driver 17 for SQL Server",
                        "TrustServerCertificate": "yes"
                    }
                )
            else:
                connection_url = URL.create(
                    "mssql+pyodbc",
                    host=self.server,
                    database=self.database,
                    query={
                        "driver": "ODBC Driver 17 for SQL Server",
                        "Trusted_Connection": "yes",
                        "TrustServerCertificate": "yes"
                    }
                )
            
            return create_engine(connection_url, pool_pre_ping=True)
        except Exception as e:
            logging.error(f"Failed to create SQLAlchemy engine: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test database connection"""
        if not PYODBC_AVAILABLE:
            logging.warning("pyodbc not available - connection test skipped")
            return False
            
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
        if not PYODBC_AVAILABLE:
            logging.warning("pyodbc not available - returning empty DataFrame")
            st.warning("Database connection not available - using test mode")
            return pd.DataFrame()
        
        # Use SQLAlchemy engine if available (recommended by pandas)
        if _self.engine is not None:
            try:
                # SQLAlchemy requires named parameters with text(), but pandas.read_sql
                # with positional params works differently - use connection directly
                with _self.engine.connect() as conn:
                    if params:
                        return pd.read_sql(query, conn, params=params)
                    else:
                        return pd.read_sql(query, conn)
            except Exception as e:
                logging.error(f"Query execution failed with SQLAlchemy: {e}")
                st.error(f"Database query failed: {str(e)}")
                return pd.DataFrame()
        else:
            # Fallback to pyodbc connection
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

        # Filter out None, empty strings, and whitespace-only values from user_projects
        user_projects = [str(p).strip() for p in user_projects if p is not None and str(p).strip()]
        if not user_projects:
            logging.warning("get_projects: No valid projects after filtering None values")
            return pd.DataFrame()

        placeholders = ','.join(['?' for _ in user_projects])
        query = f"""
        SELECT DISTINCT [Projekt], [ProjektNr], [Kundenname]
        FROM ZV
        WHERE [ProjektNr] IN ({placeholders})
        ORDER BY [Projekt]
        """
        return self.execute_query(query, tuple(user_projects))
    
    def get_time_entries(self, projects: list, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get time entries for specified projects"""
        if not projects:
            return pd.DataFrame()

        # Filter out None, empty strings, and whitespace-only values from projects
        projects = [str(p).strip() for p in projects if p is not None and str(p).strip()]
        if not projects:
            logging.warning("get_time_entries: No valid projects after filtering None values")
            return pd.DataFrame()

        where_conditions = []
        params = []

        # Project filter (using ProjektNr)
        placeholders = ','.join(['?' for _ in projects])
        where_conditions.append(f"[ProjektNr] IN ({placeholders})")
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
            if filters.get('date_range'):
                date_range = filters['date_range']
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    if start_date:
                        where_conditions.append("[Datum] >= ?")
                        params.append(start_date)
                    if end_date:
                        where_conditions.append("[Datum] <= ?")
                        params.append(end_date)

        # Robust filter: Remove None, empty strings, and ensure all items are strings
        where_conditions = [str(c) for c in where_conditions if c is not None and str(c).strip()]
        if not where_conditions:
            where_conditions = ["1=1"]

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
    
    def get_aggregated_data(self, projects: list, filters: Dict[str, Any] = None, hours_column: str = "FaktStd") -> pd.DataFrame:
        """Get aggregated time data by activity (Verwendung)"""
        if not projects:
            return pd.DataFrame()

        # Filter out None, empty strings, and whitespace-only values from projects
        projects = [str(p).strip() for p in projects if p is not None and str(p).strip()]
        if not projects:
            logging.warning("get_aggregated_data: No valid projects after filtering None values")
            return pd.DataFrame()

        where_conditions = []
        params = []

        # Project filter (using ProjektNr)
        placeholders = ','.join(['?' for _ in projects])
        where_conditions.append(f"[ProjektNr] IN ({placeholders})")
        params.extend(projects)

        # Additional filters
        if filters:
            if filters.get('year'):
                where_conditions.append("[Jahr] = ?")
                params.append(filters['year'])
            if filters.get('month'):
                where_conditions.append("[Monat] = ?")
                params.append(filters['month'])
            if filters.get('date_range'):
                date_range = filters['date_range']
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    if start_date:
                        where_conditions.append("[Datum] >= ?")
                        params.append(start_date)
                    if end_date:
                        where_conditions.append("[Datum] <= ?")
                        params.append(end_date)

        # Robust filter: Remove None, empty strings, and ensure all items are strings
        where_conditions = [str(c) for c in where_conditions if c is not None and str(c).strip()]
        if not where_conditions:
            where_conditions = ["1=1"]

        where_clause = " AND ".join(where_conditions)

        query = f"""
        SELECT
            [Projekt],
            [ProjektNr],
            [Kundenname],
            [Name],
            [Verwendung] as Activity,
            SUM(CAST([{hours_column}] as FLOAT)) as ActualHours,
            COUNT(*) as EntryCount,
            MIN([Datum]) as FirstEntry,
            MAX([Datum]) as LastEntry
        FROM ZV
        WHERE {where_clause}
        GROUP BY [Projekt], [ProjektNr], [Kundenname], [Name], [Verwendung]
        ORDER BY [Projekt], SUM(CAST([{hours_column}] as FLOAT)) DESC
        """

        return self.execute_query(query, tuple(params))

    @st.cache_data(ttl=3600)  # Cache für 1 Stunde
    def get_project_bookings(_self, projects: list, hours_column: str = "FaktStd", activity: str = None, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Lädt Buchungsdaten für Zeitreihen-Analysen.

        Args:
            projects: Liste der Projekt-IDs (ProjektNr wie P24SAN04)
            hours_column: Spalte für Stunden (Zeit oder FaktStd)
            activity: Optional Activity-Filter
            filters: Optional additional filters (date_range, etc.)

        Returns:
            DataFrame mit [DatumBuchung, Stunden, Activity, Projekt]
        """
        if not PYODBC_AVAILABLE:
            logging.warning("pyodbc not available - returning empty DataFrame")
            return pd.DataFrame()

        if not projects:
            return pd.DataFrame()

        # Filter out None, empty strings, and whitespace-only values from projects
        projects = [str(p).strip() for p in projects if p is not None and str(p).strip()]
        if not projects:
            logging.warning("get_project_bookings: No valid projects after filtering None values")
            return pd.DataFrame()

        where_conditions = []
        params = []

        # Project filter (using ProjektNr)
        placeholders = ','.join(['?' for _ in projects])
        where_conditions.append(f"[ProjektNr] IN ({placeholders})")
        params.extend(projects)

        # Activity filter
        if activity:
            where_conditions.append("[Verwendung] = ?")
            params.append(activity)

        # Additional filters
        if filters:
            if filters.get('date_range'):
                date_range = filters['date_range']
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    if start_date:
                        where_conditions.append("[Datum] >= ?")
                        params.append(start_date)
                    if end_date:
                        where_conditions.append("[Datum] <= ?")
                        params.append(end_date)

        # Robust filter: Remove None, empty strings, and ensure all items are strings
        where_conditions = [str(c) for c in where_conditions if c is not None and str(c).strip()]
        if not where_conditions:
            where_conditions = ["1=1"]

        where_clause = " AND ".join(where_conditions)

        query = f"""
        SELECT
            [DatumBuchung],
            [Projekt],
            [Verwendung] as Activity,
            CAST([{hours_column}] as FLOAT) as Stunden
        FROM ZV
        WHERE {where_clause}
        ORDER BY [DatumBuchung] ASC
        """

        return _self.execute_query(query, tuple(params))

    def validate_project_exists(self, project_id: str) -> bool:
        """
        Validiert ob ein Projektkürzel in der ZV-Tabelle existiert.

        Args:
            project_id: Projektkürzel (z.B. 'P24SAN04')

        Returns:
            True wenn Projekt existiert, False sonst
        """
        if not PYODBC_AVAILABLE:
            logging.warning("pyodbc not available - skipping validation")
            return True

        if not project_id or not project_id.strip():
            return False

        query = """
        SELECT COUNT(*) as count
        FROM ZV
        WHERE [ProjektNr] = ?
        """

        try:
            with pyodbc.connect(self.connection_string, timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (project_id.strip(),))
                result = cursor.fetchone()
                return result[0] > 0 if result else False
        except Exception as e:
            logging.error(f"Project validation failed for '{project_id}': {e}")
            return False

    # ============================================
    # Budget History Management
    # ============================================

    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        Execute non-query SQL command (INSERT, UPDATE, DELETE)

        Args:
            query: SQL command to execute
            params: Optional tuple of parameters

        Returns:
            True if successful, False otherwise
        """
        if not PYODBC_AVAILABLE:
            logging.warning("pyodbc not available - cannot execute command")
            return False

        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Command execution failed: {e}")
            st.error(f"Database command failed: {str(e)}")
            return False

    def save_budget_entry(
        self,
        project_id: str,
        activity: str,
        hours: float,
        change_type: str,
        valid_from: str,  # ISO format date string (YYYY-MM-DD)
        reason: str,
        reference: Optional[str],
        created_by: str
    ) -> bool:
        """
        Save a new budget entry to the BudgetHistory table

        Args:
            project_id: Project identifier (e.g., 'P24ABC01')
            activity: Activity name (e.g., 'Implementierung')
            hours: Number of hours for this budget entry
            change_type: Type of change ('initial', 'extension', 'correction', 'reduction')
            valid_from: Date from which this budget is valid (ISO format)
            reason: Explanation for this budget entry
            reference: Optional reference (contract number, change request, etc.)
            created_by: User email who created this entry

        Returns:
            True if successful, False otherwise
        """
        if not PYODBC_AVAILABLE:
            logging.warning("pyodbc not available - cannot save budget entry")
            return False

        query = """
        INSERT INTO BudgetHistory (
            ProjectID, Activity, Hours, ChangeType, ValidFrom,
            Reason, Reference, CreatedBy
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            project_id,
            activity,
            hours,
            change_type,
            valid_from,
            reason,
            reference if reference else None,
            created_by
        )

        return self.execute_non_query(query, params)

    def get_budget_history(
        self,
        project_id: str,
        activity: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get complete budget history for a project/activity

        Args:
            project_id: Project identifier
            activity: Optional activity filter

        Returns:
            DataFrame with budget history entries
        """
        if activity:
            query = """
            SELECT
                ID,
                ProjectID,
                Activity,
                Hours,
                ChangeType,
                ValidFrom,
                Reason,
                Reference,
                CreatedBy,
                CreatedAt
            FROM BudgetHistory
            WHERE ProjectID = ? AND Activity = ?
            ORDER BY ValidFrom DESC, CreatedAt DESC
            """
            params = (project_id, activity)
        else:
            query = """
            SELECT
                ID,
                ProjectID,
                Activity,
                Hours,
                ChangeType,
                ValidFrom,
                Reason,
                Reference,
                CreatedBy,
                CreatedAt
            FROM BudgetHistory
            WHERE ProjectID = ?
            ORDER BY Activity, ValidFrom DESC, CreatedAt DESC
            """
            params = (project_id,)

        return self.execute_query(query, params)

    def get_budget_at_date(
        self,
        project_id: str,
        activity: str,
        target_date: str  # ISO format date string (YYYY-MM-DD)
    ) -> float:
        """
        Calculate total budget for a project/activity at a specific date

        Args:
            project_id: Project identifier
            activity: Activity name
            target_date: Date for which to calculate budget (ISO format)

        Returns:
            Total budget hours valid at the target date
        """
        query = """
        SELECT COALESCE(SUM(Hours), 0) as TotalHours
        FROM BudgetHistory
        WHERE ProjectID = ?
          AND Activity = ?
          AND ValidFrom <= ?
        """

        result = self.execute_query(query, (project_id, activity, target_date))

        if not result.empty and 'TotalHours' in result.columns:
            return float(result['TotalHours'].iloc[0])
        return 0.0

    def get_all_budgets_at_date(
        self,
        projects: list,
        target_date: str  # ISO format date string (YYYY-MM-DD)
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate all budgets for multiple projects at a specific date

        Args:
            projects: List of project identifiers
            target_date: Date for which to calculate budgets (ISO format)

        Returns:
            Dictionary mapping project -> activity -> budget hours
            Example: {'P24ABC01': {'Implementierung': 150.0, 'Testing': 50.0}}
        """
        if not projects:
            return {}

        # Filter out None, empty strings, and whitespace-only values from projects
        projects = [str(p).strip() for p in projects if p is not None and str(p).strip()]
        if not projects:
            logging.warning("get_all_budgets_at_date: No valid projects after filtering None values")
            return {}

        placeholders = ','.join(['?' for _ in projects])
        query = f"""
        SELECT
            ProjectID,
            Activity,
            SUM(Hours) as TotalHours
        FROM BudgetHistory
        WHERE ProjectID IN ({placeholders})
          AND ValidFrom <= ?
        GROUP BY ProjectID, Activity
        """

        params = tuple(projects) + (target_date,)
        result = self.execute_query(query, params)

        budgets = {}
        for _, row in result.iterrows():
            project_id = row['ProjectID']
            activity = row['Activity']
            hours = float(row['TotalHours'])

            if project_id not in budgets:
                budgets[project_id] = {}
            budgets[project_id][activity] = hours

        return budgets

    def get_all_activities_for_project(self, project_id: str) -> list:
        """
        Get all unique activities that have budget entries for a project

        Args:
            project_id: Project identifier

        Returns:
            List of activity names
        """
        query = """
        SELECT DISTINCT Activity
        FROM BudgetHistory
        WHERE ProjectID = ?
        ORDER BY Activity
        """

        result = self.execute_query(query, (project_id,))

        if not result.empty and 'Activity' in result.columns:
            return result['Activity'].tolist()
        return []

# Global database instance
db_config = DatabaseConfig()
