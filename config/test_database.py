"""
Mock database for test environment with dummy data
"""
import os
import pandas as pd
import streamlit as st
import json
from typing import Optional, Dict, Any
import logging
from datetime import datetime

class TestDatabaseConfig:
    """Mock database configuration for testing with dummy data"""
    
    def __init__(self):
        self.test_data_dir = "test_data"
        self.dummy_data_loaded = False
        self.time_entries_df = pd.DataFrame()
        self.aggregated_df = pd.DataFrame()
        
        # Load dummy data on initialization
        self.load_dummy_data()
    
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
        projects = ["P24SAN06", "P24XYZ01", "P24ABC02"]
        activities = ["Analyse & Konzeption", "Implementierung", "Testing & QA", "Deployment"]
        
        # Create minimal time entries
        entries = []
        for project in projects:
            for activity in activities:
                entries.append({
                    'Name': 'Test User',
                    'Zeit': 25.5,
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
    
    def create_aggregated_data(self):
        """Create aggregated data from time entries"""
        if self.time_entries_df.empty:
            return
        
        self.aggregated_df = self.time_entries_df.groupby([
            'Projekt', 'ProjektNr', 'Kundenname', 'Verwendung'
        ]).agg({
            'Zeit': 'sum',
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
    
    def get_aggregated_data_mock(self, params: Optional[tuple] = None) -> pd.DataFrame:
        """Mock aggregated data"""
        if self.aggregated_df.empty:
            return pd.DataFrame()
        
        df = self.aggregated_df.copy()
        
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
    
    def get_aggregated_data(self, projects: list, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get aggregated time data by activity"""
        params = list(projects)
        
        # Add filter params
        if filters:
            if filters.get('year'):
                params.append(filters['year'])
            if filters.get('month'):
                params.append(filters['month'])
        
        return self.get_aggregated_data_mock(tuple(params))
    
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

# Global test database instance
test_db_config = TestDatabaseConfig()
