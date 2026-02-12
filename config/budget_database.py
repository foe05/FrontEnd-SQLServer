"""
SQLite database for budget management
Separate from SQL Server to allow read-only access to time tracking data
"""
import os
import sqlite3
import pandas as pd
import logging
from typing import Optional, Dict, List
from datetime import datetime
import streamlit as st


class BudgetDatabaseConfig:
    """SQLite database configuration for budget management"""

    def __init__(self, db_path: str = "data/budget.db"):
        self.db_path = db_path
        self.ensure_db_directory()
        self.ensure_tables_exist()

    def ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logging.info(f"Created database directory: {db_dir}")

    def get_connection(self):
        """Get SQLite database connection"""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def ensure_tables_exist(self):
        """Ensure all required tables exist, create if not"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Check if BudgetHistory table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='BudgetHistory'
                """)

                if not cursor.fetchone():
                    # Create BudgetHistory table
                    cursor.execute("""
                        CREATE TABLE BudgetHistory (
                            ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            ProjectID TEXT NOT NULL,
                            Activity TEXT NOT NULL,
                            Hours REAL NOT NULL CHECK(Hours >= 0),
                            ChangeType TEXT NOT NULL CHECK(
                                ChangeType IN ('initial', 'extension', 'correction', 'reduction')
                            ),
                            ValidFrom DATE NOT NULL,
                            Reason TEXT NOT NULL,
                            Reference TEXT,
                            CreatedBy TEXT NOT NULL,
                            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Create indexes for performance
                    cursor.execute("""
                        CREATE INDEX idx_budget_project_activity
                        ON BudgetHistory(ProjectID, Activity, ValidFrom DESC)
                    """)

                    cursor.execute("""
                        CREATE INDEX idx_budget_validfrom
                        ON BudgetHistory(ValidFrom)
                    """)

                    cursor.execute("""
                        CREATE INDEX idx_budget_createdat
                        ON BudgetHistory(CreatedAt DESC)
                    """)

                    conn.commit()
                    logging.info("✅ BudgetHistory table created successfully in SQLite")

        except Exception as e:
            logging.error(f"Error ensuring tables exist: {e}")
            raise

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logging.error(f"Database connection test failed: {e}")
            return False

    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        try:
            with self.get_connection() as conn:
                if params:
                    return pd.read_sql_query(query, conn, params=params)
                else:
                    return pd.read_sql_query(query, conn)
        except Exception as e:
            logging.error(f"Query execution failed: {e}")
            return pd.DataFrame()

    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """Execute non-query SQL command (INSERT, UPDATE, DELETE)"""
        try:
            with self.get_connection() as conn:
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

    # ============================================
    # Budget History Management
    # ============================================

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

    def get_database_info(self) -> Dict[str, any]:
        """Get information about the budget database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get table count
                cursor.execute("""
                    SELECT COUNT(*) FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                table_count = cursor.fetchone()[0]

                # Get budget entry count
                cursor.execute("SELECT COUNT(*) FROM BudgetHistory")
                budget_count = cursor.fetchone()[0]

                # Get database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

                # Get unique projects
                cursor.execute("SELECT COUNT(DISTINCT ProjectID) FROM BudgetHistory")
                project_count = cursor.fetchone()[0]

                return {
                    'db_path': self.db_path,
                    'db_size_bytes': db_size,
                    'db_size_mb': round(db_size / (1024 * 1024), 2),
                    'table_count': table_count,
                    'budget_entries': budget_count,
                    'unique_projects': project_count,
                    'connection_ok': True
                }

        except Exception as e:
            logging.error(f"Error getting database info: {e}")
            return {
                'db_path': self.db_path,
                'connection_ok': False,
                'error': str(e)
            }


# Global budget database instance
budget_db = BudgetDatabaseConfig()
