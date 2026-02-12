"""
Mock database for test environment with dummy data
"""
import os
import pandas as pd
import streamlit as st
import json
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta

class TestDatabaseConfig:
    """Mock database configuration for testing with dummy data"""

    def __init__(self):
        self.test_data_dir = "test_data"
        self.dummy_data_loaded = False
        self.time_entries_df = pd.DataFrame()
        self.aggregated_df = pd.DataFrame()

        # In-memory budget history for test mode
        self.budget_history = []
        self.budget_id_counter = 1

        # Load dummy data on initialization
        self.load_dummy_data()
        self._initialize_test_budgets()
    
    def load_dummy_data(self):
        """Load dummy data from files"""
        try:
            # Load time entries
            csv_path = os.path.join(self.test_data_dir, "zv_dummy_data.csv")
            json_path = os.path.join(self.test_data_dir, "zv_dummy_data.json")
            
            if os.path.exists(csv_path):
                self.time_entries_df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
                logging.info(f"Loaded {len(self.time_entries_df)} time entries from CSV")
            elif os.path.exists(json_path):
                self.time_entries_df = pd.read_json(json_path)
                logging.info(f"Loaded {len(self.time_entries_df)} time entries from JSON")
            else:
                # Generate dummy data if files don't exist
                self.generate_dummy_data()
            
            # Load aggregated data
            agg_csv_path = os.path.join(self.test_data_dir, "zv_aggregated_dummy.csv")
            agg_json_path = os.path.join(self.test_data_dir, "zv_aggregated_dummy.json")
            
            if os.path.exists(agg_csv_path):
                self.aggregated_df = pd.read_csv(agg_csv_path, sep=';', encoding='utf-8')
                logging.info(f"Loaded {len(self.aggregated_df)} aggregated entries from CSV")
            elif os.path.exists(agg_json_path):
                self.aggregated_df = pd.read_json(agg_json_path)
                logging.info(f"Loaded {len(self.aggregated_df)} aggregated entries from JSON")
            else:
                # Generate aggregated data from time entries
                if not self.time_entries_df.empty:
                    self.create_aggregated_data()
            
            self.dummy_data_loaded = True
            
        except Exception as e:
            logging.error(f"Error loading dummy data: {e}")
            self.generate_minimal_dummy_data()
    
    def generate_dummy_data(self):
        """Generate dummy data using the generator"""
        try:
            from test_data.dummy_data_generator import DummyDataGenerator
            generator = DummyDataGenerator()
            data = generator.save_dummy_data(self.test_data_dir)
            
            self.time_entries_df = data['time_entries']
            self.aggregated_df = data['aggregated']
            
        except ImportError:
            logging.warning("Dummy data generator not available, using minimal data")
            self.generate_minimal_dummy_data()
    
    def generate_minimal_dummy_data(self):
        """Generate minimal dummy data if generator fails"""
        projects = ["P24ABC01", "P24XYZ01", "P24DEF02"]
        activities = ["Analyse & Konzeption", "Implementierung", "Testing & QA", "Deployment"]
        
        # Create minimal time entries
        entries = []
        for project in projects:
            for activity in activities:
                entries.append({
                    'Name': 'Test User',
                    'FaktStd': 25.5,
                    'Projekt': project,
                    'Verwendung': activity,
                    'Kundenname': f'Kunde {project}',
                    'ProjektNr': f'{project}-NR',
                    'Status': 'Genehmigt',
                    'Datum': '2024-01-15',
                    'Jahr': 2024,
                    'Monat': 1
                })
        
        self.time_entries_df = pd.DataFrame(entries)
        self.create_aggregated_data()
    
    def create_aggregated_data(self, hours_column: str = "FaktStd"):
        """Create aggregated data from time entries"""
        if self.time_entries_df.empty:
            return
        
        self.aggregated_df = self.time_entries_df.groupby([
            'Projekt', 'ProjektNr', 'Kundenname', 'Verwendung'
        ]).agg({
            hours_column: 'sum',  # Use the specified column
            'Name': 'count',
            'Datum': ['min', 'max']
        }).round(2)
        
        # Flatten column names
        self.aggregated_df.columns = ['ActualHours', 'EntryCount', 'FirstEntry', 'LastEntry']
        self.aggregated_df = self.aggregated_df.reset_index()
        self.aggregated_df['Activity'] = self.aggregated_df['Verwendung']
    
    def test_connection(self) -> bool:
        """Test connection (always True for test environment)"""
        return not self.time_entries_df.empty
    
    @st.cache_data(ttl=60)  # Cache for 1 minute in test mode
    def execute_query(_self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Mock query execution - return dummy data"""
        # For test environment, we don't actually execute SQL
        # Instead, we return appropriate dummy data based on the context
        logging.info(f"Mock query execution: {query[:100]}...")
        
        if "DISTINCT" in query and "Projekt" in query:
            # Project query
            return _self.get_projects_mock(params)
        elif "GROUP BY" in query:
            # Aggregated query
            return _self.get_aggregated_data_mock(params)
        else:
            # Detail query
            return _self.get_time_entries_mock(params)
    
    def get_projects_mock(self, params: Optional[tuple] = None) -> pd.DataFrame:
        """Mock project data"""
        if self.time_entries_df.empty:
            return pd.DataFrame()
        
        projects_df = self.time_entries_df[['Projekt', 'ProjektNr', 'Kundenname']].drop_duplicates()
        
        # Apply project filter if provided
        if params and len(params) > 0:
            # Filter by user projects (params contains the project list)
            user_projects = list(params)
            projects_df = projects_df[projects_df['Projekt'].isin(user_projects)]
        
        return projects_df.sort_values('Projekt')
    
    def get_time_entries_mock(self, params: Optional[tuple] = None) -> pd.DataFrame:
        """Mock time entries data"""
        if self.time_entries_df.empty:
            return pd.DataFrame()
        
        df = self.time_entries_df.copy()
        
        # Apply basic filtering based on params
        if params and len(params) > 0:
            # First params are usually project filters
            project_count = 0
            while project_count < len(params) and isinstance(params[project_count], str) and params[project_count].startswith('P24'):
                project_count += 1
            
            if project_count > 0:
                user_projects = list(params[:project_count])
                df = df[df['Projekt'].isin(user_projects)]
            
            # Apply additional filters (year, month, etc.)
            if len(params) > project_count:
                remaining_params = params[project_count:]
                for param in remaining_params:
                    if isinstance(param, int):
                        if param > 2020 and param < 2030:  # Year filter
                            df = df[df['Jahr'] == param]
                        elif param >= 1 and param <= 12:  # Month filter
                            df = df[df['Monat'] == param]
        
        return df
    
    def get_aggregated_data_mock(self, params: Optional[tuple] = None, hours_column: str = "FaktStd") -> pd.DataFrame:
        """Mock aggregated data"""
        if self.time_entries_df.empty:
            return pd.DataFrame()
        
        # Recreate aggregated data with the specified hours column
        aggregated_df = self.time_entries_df.groupby([
            'Projekt', 'ProjektNr', 'Kundenname', 'Verwendung'
        ]).agg({
            hours_column: 'sum',  # Use the specified column
            'Name': 'count',
            'Datum': ['min', 'max']
        }).round(2)
        
        # Flatten column names
        aggregated_df.columns = ['ActualHours', 'EntryCount', 'FirstEntry', 'LastEntry']
        aggregated_df = aggregated_df.reset_index()
        aggregated_df['Activity'] = aggregated_df['Verwendung']
        
        df = aggregated_df.copy()
        
        # Apply project filtering
        if params and len(params) > 0:
            project_count = 0
            while project_count < len(params) and isinstance(params[project_count], str) and params[project_count].startswith('P24'):
                project_count += 1
            
            if project_count > 0:
                user_projects = list(params[:project_count])
                df = df[df['Projekt'].isin(user_projects)]
        
        return df
    
    def get_projects(self, user_projects: list) -> pd.DataFrame:
        """Get available projects for user"""
        return self.get_projects_mock(tuple(user_projects))
    
    def get_time_entries(self, projects: list, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get time entries for specified projects"""
        params = list(projects)
        
        # Add filter params
        if filters:
            if filters.get('year'):
                params.append(filters['year'])
            if filters.get('month'):
                params.append(filters['month'])
        
        return self.get_time_entries_mock(tuple(params))
    
    def get_aggregated_data(self, projects: list, filters: Dict[str, Any] = None, hours_column: str = "FaktStd") -> pd.DataFrame:
        """Get aggregated time data by activity"""
        params = list(projects)
        
        # Add filter params
        if filters:
            if filters.get('year'):
                params.append(filters['year'])
            if filters.get('month'):
                params.append(filters['month'])
        
        return self.get_aggregated_data_mock(tuple(params), hours_column)
    
    def get_data_info(self) -> Dict[str, Any]:
        """Get information about loaded dummy data"""
        return {
            'time_entries_count': len(self.time_entries_df),
            'aggregated_count': len(self.aggregated_df),
            'projects': self.time_entries_df['Projekt'].nunique() if not self.time_entries_df.empty else 0,
            'activities': self.time_entries_df['Verwendung'].nunique() if not self.time_entries_df.empty else 0,
            'date_range': {
                'min': self.time_entries_df['Datum'].min() if not self.time_entries_df.empty else None,
                'max': self.time_entries_df['Datum'].max() if not self.time_entries_df.empty else None
            } if not self.time_entries_df.empty else None,
            'dummy_data_loaded': self.dummy_data_loaded
        }

    def get_project_bookings(self, projects: list, hours_column: str = "FaktStd", activity: str = None) -> pd.DataFrame:
        """
        Lädt Buchungsdaten für Zeitreihen-Analysen (TEST MODE).
        
        Args:
            projects: Liste der Projekt-IDs
            hours_column: Spalte für Stunden (Zeit oder FaktStd)
            activity: Optional Activity-Filter
            
        Returns:
            DataFrame mit [DatumBuchung, Stunden, Activity, Projekt]
        """
        if self.time_entries_df.empty:
            # Generate timeseries if not available
            return self.generate_timeseries_dummy_data(projects, hours_column, activity)
        
        # Filter by projects
        df = self.time_entries_df[self.time_entries_df['Projekt'].isin(projects)].copy()
        
        # Filter by activity if specified
        if activity:
            df = df[df['Verwendung'] == activity]
        
        # Select and rename columns
        result_df = df[['Datum', 'Projekt', 'Verwendung', hours_column]].copy()
        result_df.columns = ['DatumBuchung', 'Projekt', 'Activity', 'Stunden']
        result_df['DatumBuchung'] = pd.to_datetime(result_df['DatumBuchung'])
        
        return result_df.sort_values('DatumBuchung')
    
    def generate_timeseries_dummy_data(self, projects: list, hours_column: str = "FaktStd", activity: str = None) -> pd.DataFrame:
        """Generate realistic sprint-based timeseries dummy data for charts"""
        import numpy as np
        
        # Generiere Daten für letzte 8 Wochen (4 Sprints) bis heute
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=8)
        
        data = []
        
        for project in projects:
            activities = ['Analyse & Konzeption', 'Implementierung', 'Testing & QA', 'Deployment']
            
            for act in activities:
                if activity and act != activity:
                    continue
                
                # 4 Sprints à 2 Wochen mit realistischer Velocity-Variation
                for sprint in range(4):
                    sprint_start = start_date + timedelta(weeks=sprint * 2)
                    
                    # Sprint-Velocity variiert (realistisch)
                    # Basis: 80h pro Sprint mit Variation
                    base_velocity = 80
                    sprint_velocity = base_velocity + np.random.uniform(-15, 20)
                    
                    # Verteilung über Arbeitstage (Mo-Fr)
                    work_days = []
                    for day_offset in range(14):
                        day = sprint_start + timedelta(days=day_offset)
                        if day.weekday() < 5 and day <= end_date:  # Nur bis heute
                            work_days.append(day)
                    
                    if not work_days:
                        continue
                    
                    # Verteile Sprint-Velocity auf Arbeitstage
                    for day in work_days:
                        # Realistische Schwankung pro Tag (60-140% vom Durchschnitt)
                        avg_per_day = sprint_velocity / len(work_days)
                        daily_hours = avg_per_day * np.random.uniform(0.6, 1.4)
                        
                        # Begrenzen auf 0-10h pro Tag
                        daily_hours = max(0, min(10, daily_hours))
                        
                        data.append({
                            'DatumBuchung': day,
                            'Projekt': project,
                            'Activity': act,
                            'Stunden': round(daily_hours, 1)
                        })
        
        df = pd.DataFrame(data)
        return df.sort_values('DatumBuchung') if not df.empty else df

    # ============================================
    # Budget History Management (Test Mode)
    # ============================================

    def _initialize_test_budgets(self):
        """Initialize some test budget entries"""
        test_budgets = [
            {
                'ProjectID': 'P24ABC01',
                'Activity': 'Implementierung',
                'Hours': 100.0,
                'ChangeType': 'initial',
                'ValidFrom': '2024-01-01',
                'Reason': 'Initialisiertes Testbudget',
                'Reference': 'TEST-001',
                'CreatedBy': 'test@example.com',
                'CreatedAt': '2024-01-01 10:00:00'
            },
            {
                'ProjectID': 'P24ABC01',
                'Activity': 'Testing & QA',
                'Hours': 50.0,
                'ChangeType': 'initial',
                'ValidFrom': '2024-01-01',
                'Reason': 'Initialisiertes Testbudget',
                'Reference': 'TEST-001',
                'CreatedBy': 'test@example.com',
                'CreatedAt': '2024-01-01 10:00:00'
            },
            {
                'ProjectID': 'P24XYZ01',
                'Activity': 'Implementierung',
                'Hours': 80.0,
                'ChangeType': 'initial',
                'ValidFrom': '2024-01-01',
                'Reason': 'Initialisiertes Testbudget',
                'Reference': 'TEST-002',
                'CreatedBy': 'test@example.com',
                'CreatedAt': '2024-01-01 10:00:00'
            }
        ]

        for budget in test_budgets:
            budget['ID'] = self.budget_id_counter
            self.budget_id_counter += 1
            self.budget_history.append(budget)

    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        Mock non-query execution for test mode

        Args:
            query: SQL command (ignored in test mode)
            params: Parameters for the command

        Returns:
            Always True in test mode
        """
        logging.info(f"Mock non-query execution: {query[:100]}...")
        return True

    def save_budget_entry(
        self,
        project_id: str,
        activity: str,
        hours: float,
        change_type: str,
        valid_from: str,
        reason: str,
        reference: Optional[str],
        created_by: str
    ) -> bool:
        """
        Save a new budget entry to in-memory storage (test mode)

        Args:
            project_id: Project identifier
            activity: Activity name
            hours: Number of hours
            change_type: Type of change
            valid_from: Valid from date (ISO format)
            reason: Explanation
            reference: Optional reference
            created_by: User email

        Returns:
            True if successful
        """
        try:
            entry = {
                'ID': self.budget_id_counter,
                'ProjectID': project_id,
                'Activity': activity,
                'Hours': hours,
                'ChangeType': change_type,
                'ValidFrom': valid_from,
                'Reason': reason,
                'Reference': reference,
                'CreatedBy': created_by,
                'CreatedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            self.budget_history.append(entry)
            self.budget_id_counter += 1

            logging.info(f"Saved budget entry: {project_id} - {activity} - {hours}h")
            return True

        except Exception as e:
            logging.error(f"Error saving budget entry: {e}")
            return False

    def get_budget_history(
        self,
        project_id: str,
        activity: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get budget history from in-memory storage (test mode)

        Args:
            project_id: Project identifier
            activity: Optional activity filter

        Returns:
            DataFrame with budget history
        """
        # Filter by project
        filtered = [b for b in self.budget_history if b['ProjectID'] == project_id]

        # Filter by activity if specified
        if activity:
            filtered = [b for b in filtered if b['Activity'] == activity]

        if not filtered:
            return pd.DataFrame()

        df = pd.DataFrame(filtered)

        # Sort by ValidFrom descending, then CreatedAt descending
        df['ValidFrom_dt'] = pd.to_datetime(df['ValidFrom'])
        df['CreatedAt_dt'] = pd.to_datetime(df['CreatedAt'])
        df = df.sort_values(['ValidFrom_dt', 'CreatedAt_dt'], ascending=[False, False])
        df = df.drop(['ValidFrom_dt', 'CreatedAt_dt'], axis=1)

        return df

    def get_budget_at_date(
        self,
        project_id: str,
        activity: str,
        target_date: str
    ) -> float:
        """
        Calculate total budget at a specific date (test mode)

        Args:
            project_id: Project identifier
            activity: Activity name
            target_date: Target date (ISO format)

        Returns:
            Total budget hours valid at target date
        """
        target_dt = datetime.fromisoformat(target_date)

        # Filter entries
        filtered = [
            b for b in self.budget_history
            if b['ProjectID'] == project_id
            and b['Activity'] == activity
            and datetime.fromisoformat(b['ValidFrom']) <= target_dt
        ]

        # Sum hours
        total = sum(b['Hours'] for b in filtered)
        return total

    def get_all_budgets_at_date(
        self,
        projects: list,
        target_date: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate all budgets for multiple projects at a specific date (test mode)

        Args:
            projects: List of project identifiers
            target_date: Target date (ISO format)

        Returns:
            Dictionary mapping project -> activity -> budget hours
        """
        target_dt = datetime.fromisoformat(target_date)
        budgets = {}

        for entry in self.budget_history:
            if entry['ProjectID'] not in projects:
                continue

            valid_from_dt = datetime.fromisoformat(entry['ValidFrom'])
            if valid_from_dt > target_dt:
                continue

            project_id = entry['ProjectID']
            activity = entry['Activity']
            hours = entry['Hours']

            if project_id not in budgets:
                budgets[project_id] = {}

            if activity not in budgets[project_id]:
                budgets[project_id][activity] = 0.0

            budgets[project_id][activity] += hours

        return budgets

    def get_all_activities_for_project(self, project_id: str) -> list:
        """
        Get all unique activities for a project (test mode)

        Args:
            project_id: Project identifier

        Returns:
            List of activity names
        """
        activities = set()

        for entry in self.budget_history:
            if entry['ProjectID'] == project_id:
                activities.add(entry['Activity'])

        return sorted(list(activities))

# Global test database instance
test_db_config = TestDatabaseConfig()
