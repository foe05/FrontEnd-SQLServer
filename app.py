"""
Main Streamlit application for SQL Server Dashboard
"""
import streamlit as st
import pandas as pd
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Page configuration MUST be first Streamlit command
st.set_page_config(
    page_title="SQL Server Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global custom CSS styling based on the design system
def apply_custom_styles():
    """Apply custom CSS styling inspired by the Executive Dashboard design"""
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        /* Global Font */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Primary Color */
        :root {
            --primary-color: #135bec;
            --background-light: #f8f9fc;
            --card-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        }

        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Main container */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }

        /* Custom KPI Card */
        .kpi-card {
            background: white;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: var(--card-shadow);
            border: 1px solid #e2e8f0;
            position: relative;
            overflow: hidden;
            transition: all 0.2s;
        }

        .kpi-card:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        .kpi-card-icon {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: rgba(19, 91, 236, 0.1);
            padding: 0.75rem;
            border-radius: 0.75rem;
        }

        .kpi-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }

        .kpi-value {
            font-size: 2rem;
            font-weight: 800;
            color: #0f172a;
            line-height: 1;
        }

        .kpi-trend {
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }

        .kpi-trend.positive {
            color: #10b981;
        }

        .kpi-trend.negative {
            color: #ef4444;
        }

        .kpi-trend.neutral {
            color: #64748b;
        }

        /* Status Badges */
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.375rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .status-badge.success {
            background-color: #d1fae5;
            color: #065f46;
        }

        .status-badge.warning {
            background-color: #fef3c7;
            color: #92400e;
        }

        .status-badge.danger {
            background-color: #fee2e2;
            color: #991b1b;
        }

        .status-badge.info {
            background-color: #dbeafe;
            color: #1e40af;
        }

        /* Custom Tables */
        .dataframe {
            border: none !important;
        }

        .dataframe thead tr th {
            background-color: #f8fafc !important;
            color: #64748b !important;
            font-size: 0.75rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 1rem 1.5rem !important;
            border: none !important;
        }

        .dataframe tbody tr {
            border-bottom: 1px solid #f1f5f9 !important;
            transition: background-color 0.2s;
        }

        .dataframe tbody tr:hover {
            background-color: #f8fafc !important;
        }

        .dataframe tbody tr td {
            padding: 1rem 1.5rem !important;
            border: none !important;
            font-size: 0.875rem;
        }

        /* Custom Buttons */
        .stButton > button {
            background-color: var(--primary-color);
            color: white;
            border-radius: 0.5rem;
            padding: 0.625rem 1.25rem;
            font-weight: 600;
            border: none;
            box-shadow: 0 4px 6px -1px rgba(19, 91, 236, 0.2);
            transition: all 0.2s;
        }

        .stButton > button:hover {
            background-color: #0d47a1;
            box-shadow: 0 10px 15px -3px rgba(19, 91, 236, 0.3);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background-color: transparent;
            border-bottom: 2px solid #e2e8f0;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1.5rem;
            background-color: transparent;
            border-radius: 0.5rem 0.5rem 0 0;
            font-weight: 600;
            color: #64748b;
        }

        .stTabs [aria-selected="true"] {
            background-color: white;
            color: var(--primary-color);
            border-bottom: 3px solid var(--primary-color);
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: white;
            border-right: 1px solid #e2e8f0;
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 2rem;
        }

        /* Metrics */
        [data-testid="stMetric"] {
            background-color: white;
            padding: 1.5rem;
            border-radius: 1rem;
            box-shadow: var(--card-shadow);
            border: 1px solid #e2e8f0;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.875rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
        }

        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 800;
            color: #0f172a;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background-color: white;
            border-radius: 0.75rem;
            border: 1px solid #e2e8f0;
            padding: 1rem;
            font-weight: 600;
            color: #0f172a;
        }

        .streamlit-expanderContent {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-top: none;
            border-radius: 0 0 0.75rem 0.75rem;
        }

        /* Info boxes */
        .stAlert {
            border-radius: 0.75rem;
            border: 1px solid;
        }

        /* Chart container */
        .chart-container {
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--card-shadow);
            border: 1px solid #e2e8f0;
        }

        /* Section headers */
        .section-header {
            font-size: 1.5rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #e2e8f0;
        }

        /* Project badge */
        .project-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background-color: #f1f5f9;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.75rem;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
    </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# Import custom components AFTER page config
from components.auth import auth_manager
from components.filters import filter_manager
from components.export import excel_exporter
from components.admin_user_manager import admin_user_manager
from components.skeleton_loaders import show_table_skeleton
from components.budget_manager import budget_manager
from components.burndown_chart import (
    render_burndown_chart,
    render_weekly_trend,
    show_forecast_metrics,
    render_activity_comparison,
    render_cumulative_comparison
)
from components.forecast_ui import (
    render_forecast_scenarios,
    render_scenario_chart,
    render_sprint_velocity_chart
)
from utils.cache import cache_manager
from utils.health import health_checker
from utils.forecast_engine import ForecastEngine

# Import database config based on environment
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

if TEST_MODE:
    from config.test_database import test_db_config as db_config
    from config.test_database import test_db_config as budget_db
    st.sidebar.success("🧪 TEST-MODUS AKTIV")
else:
    from config.database import db_config
    from config.budget_database import budget_db

# Helper Functions for Modern UI Components
def render_kpi_card(label: str, value: str, icon: str, trend: str = None, trend_type: str = "neutral"):
    """Render a modern KPI card with icon and optional trend"""
    trend_class = f"kpi-trend {trend_type}" if trend else ""
    trend_html = f'<div class="{trend_class}">{trend}</div>' if trend else ""

    html = f"""
    <div class="kpi-card">
        <div class="kpi-card-icon">
            <span class="material-icons" style="color: #135bec; font-size: 1.5rem;">{icon}</span>
        </div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {trend_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_status_badge(status: str) -> str:
    """Return HTML for a status badge"""
    if status == "🟢 Buchbar" or "On Track" in status:
        badge_class = "success"
        text = "On Track"
    elif status == "🟡 Kritisch" or "At Risk" in status:
        badge_class = "warning"
        text = "At Risk"
    elif status == "🔴 Überbucht" or "Critical" in status:
        badge_class = "danger"
        text = "Critical"
    else:
        badge_class = "info"
        text = status

    return f'<span class="status-badge {badge_class}">{text}</span>'

def render_project_badge(project_id: str):
    """Render a project identification badge"""
    html = f"""
    <div class="project-badge">
        <span class="material-icons" style="font-size: 1rem; color: #135bec;">folder_open</span>
        {project_id}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_section_header(title: str, subtitle: str = None):
    """Render a section header with optional subtitle"""
    subtitle_html = f'<p style="color: #64748b; font-size: 0.875rem; margin-top: 0.5rem;">{subtitle}</p>' if subtitle else ""
    html = f"""
    <div style="margin-bottom: 2rem;">
        <h2 class="section-header">{title}</h2>
        {subtitle_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

class TimeTrackingApp:
    """Main application class"""

    def __init__(self):
        self.target_hours_file = "cache/target_hours.json"

    def load_target_hours(self, projects: list = None, target_date: str = None) -> Dict[str, Dict[str, float]]:
        """
        Load target hours from SQL database with time-based validity

        Args:
            projects: Optional list of projects to load budgets for
            target_date: Optional date for budget calculation (ISO format). Defaults to today.

        Returns:
            Dictionary mapping project -> activity -> budget hours
        """
        if target_date is None:
            target_date = datetime.now().date().isoformat()

        if projects:
            # Load from SQLite budget database with time-based validity
            return budget_db.get_all_budgets_at_date(projects, target_date)
        else:
            # Fallback: Load from legacy cache system
            # This is kept for backwards compatibility during migration
            legacy_budgets = cache_manager.load_all_target_hours()
            return legacy_budgets if legacy_budgets else {}

    def save_target_hours(self, project: str, activity: str, target_hours: float):
        """
        Save target hours - deprecated, use budget_manager instead

        This method is kept for backwards compatibility but should be replaced
        with the new budget management system which includes full history tracking.
        """
        # For now, save to both systems during transition
        cache_manager.save_target_hours(project, activity, target_hours)

        # Also save to SQLite budget database as an 'adjustment' entry
        # Note: This creates a simple entry without full documentation
        # Users should use the Budget Management tab for proper tracking
        try:
            budget_db.save_budget_entry(
                project_id=project,
                activity=activity,
                hours=target_hours,
                change_type='correction',
                valid_from=datetime.now().date().isoformat(),
                reason='Quick edit from dashboard (legacy)',
                reference=None,
                created_by=st.session_state.get('user_email', 'unknown')
            )
        except Exception as e:
            logging.error(f"Error saving to SQLite budget system: {e}")
    
    def calculate_fulfillment_status(self, actual: float, target: float) -> str:
        """Calculate fulfillment status with traffic light colors"""
        if target == 0:
            return "🔴 Kein Ziel"
        
        fulfillment_pct = (actual / target) * 100
        
        if fulfillment_pct <= 100:
            return "🟢 Buchbar"
        elif fulfillment_pct <= 110:
            return "🟡 Kritisch"
        else:
            return "🔴 Überbucht"
    
    def create_dashboard_table(self, df: pd.DataFrame, target_date: str = None) -> pd.DataFrame:
        """
        Create the main dashboard table with time-based target hours

        Args:
            df: DataFrame with actual hours data
            target_date: Date for budget calculation (ISO format). Defaults to today.

        Returns:
            DataFrame with dashboard data
        """
        if df.empty:
            return pd.DataFrame()

        if target_date is None:
            target_date = datetime.now().date().isoformat()

        # Get unique projects from data
        projects = df['Projekt'].unique().tolist()

        # Load target hours for these projects at the specified date
        all_targets = self.load_target_hours(projects, target_date)
        
        dashboard_data = []
        
        # Group by project first, then by activity
        for projekt in df['Projekt'].unique():
            projekt_df = df[df['Projekt'] == projekt]
            
            # Calculate total target hours for this project
            project_total_target = sum(all_targets.get(projekt, {}).values())
            
            for activity in projekt_df['Activity'].unique():
                activity_df = projekt_df[projekt_df['Activity'] == activity]
                
                actual_hours = activity_df['ActualHours'].sum()
                
                # Get target hours from cache/filesystem (default: 0.0)
                target_hours = all_targets.get(projekt, {}).get(activity, 0.0)
                
                # Calculate fulfillment percentage
                fulfillment_pct = (actual_hours / target_hours * 100) if target_hours > 0 else 0
                
                # Calculate percentage of total project target
                project_percentage = (target_hours / project_total_target * 100) if project_total_target > 0 else 0
                
                # Determine status
                status = self.calculate_fulfillment_status(actual_hours, target_hours)
                
                dashboard_data.append({
                    'Projekt': projekt,
                    'Tätigkeit/Activity': activity,
                    'Sollstunden': target_hours,
                    'Anteil am Projekt (%)': round(project_percentage, 1),
                    'Erfüllungsstand (%)': round(fulfillment_pct, 1),
                    'Status': status,
                    'Iststunden': round(actual_hours, 1),
                    'Kunde': activity_df['Kundenname'].iloc[0] if len(activity_df) > 0 else ''
                })
        
        return pd.DataFrame(dashboard_data)
    
    def create_project_summary(self, df: pd.DataFrame, target_date: str = None) -> pd.DataFrame:
        """
        Create project summary with time-based total target vs actual hours

        Args:
            df: DataFrame with actual hours data
            target_date: Date for budget calculation (ISO format). Defaults to today.

        Returns:
            DataFrame with project summary
        """
        if df.empty:
            return pd.DataFrame()

        if target_date is None:
            target_date = datetime.now().date().isoformat()

        # Get unique projects from data
        projects = df['Projekt'].unique().tolist()

        # Load target hours for these projects at the specified date
        all_targets = self.load_target_hours(projects, target_date)
        
        summary_data = []
        
        # Group by project
        for projekt in df['Projekt'].unique():
            projekt_df = df[df['Projekt'] == projekt]
            
            # Calculate total actual hours for this project
            total_actual_hours = projekt_df['ActualHours'].sum()
            
            # Calculate total target hours for this project
            project_targets = all_targets.get(projekt, {})
            total_target_hours = sum(project_targets.values()) if project_targets else 0.0
            
            # Calculate project fulfillment
            project_fulfillment_pct = (total_actual_hours / total_target_hours * 100) if total_target_hours > 0 else 0
            
            # Determine project status
            project_status = self.calculate_fulfillment_status(total_actual_hours, total_target_hours)
            
            # Get customer name
            kunde = projekt_df['Kundenname'].iloc[0] if len(projekt_df) > 0 else ''
            
            summary_data.append({
                'Projekt': projekt,
                'Kunde': kunde,
                'Sollstunden Gesamt': round(total_target_hours, 1),
                'Iststunden Gesamt': round(total_actual_hours, 1),
                'Erfüllungsstand (%)': round(project_fulfillment_pct, 1),
                'Status': project_status,
                'Anzahl Tätigkeiten': projekt_df['Activity'].nunique()
            })
        
        return pd.DataFrame(summary_data)
    
    def show_editable_dashboard(self, dashboard_df: pd.DataFrame):
        """Show the main dashboard with editable target hours - Modern Design"""

        # Check if data is still loading
        if st.session_state.get('data_loading', False):
            show_table_skeleton(num_rows=10, num_columns=8)
            return pd.DataFrame()

        if dashboard_df.empty:
            st.markdown("""
            <div class="kpi-card" style="background: #fef3c7; border-color: #fbbf24;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <span class="material-icons" style="color: #92400e; font-size: 2rem;">info</span>
                    <div>
                        <div style="font-weight: 700; color: #92400e;">Keine Daten verfügbar</div>
                        <div style="color: #92400e; margin-top: 0.5rem; font-size: 0.875rem;">Bitte passen Sie Ihre Filter an</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return dashboard_df

        # Track all edited data across projects
        all_edited_data = []

        # Group by project
        project_list = list(dashboard_df['Projekt'].unique())
        for idx, projekt in enumerate(project_list):
            project_df = dashboard_df[dashboard_df['Projekt'] == projekt].copy()

            # Calculate project summary metrics
            project_total_target = project_df['Sollstunden'].sum()
            project_total_actual = project_df['Iststunden'].sum()
            project_activities_count = len(project_df)
            project_fulfillment = (project_total_actual / project_total_target * 100) if project_total_target > 0 else 0
            project_kunde = project_df['Kunde'].iloc[0] if len(project_df) > 0 else ''
            project_status = self.calculate_fulfillment_status(project_total_actual, project_total_target)

            # Add prominent project header with modern design
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #135bec 0%, #0d47a1 100%); padding: 1.5rem; border-radius: 1rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(19, 91, 236, 0.2);">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <span class="material-icons" style="color: white; font-size: 2rem;">folder_open</span>
                    <div>
                        <h3 style="color: white; font-size: 1.5rem; font-weight: 700; margin: 0;">{projekt}</h3>
                        <p style="color: rgba(255, 255, 255, 0.8); font-size: 0.875rem; margin: 0;">{project_kunde}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Display project summary metrics in styled cards
            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
            with summary_col1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Tätigkeiten</div>
                    <div class="kpi-value">{project_activities_count}</div>
                </div>
                """, unsafe_allow_html=True)
            with summary_col2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Sollstunden Gesamt</div>
                    <div class="kpi-value">{project_total_target:.1f}h</div>
                </div>
                """, unsafe_allow_html=True)
            with summary_col3:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Iststunden Gesamt</div>
                    <div class="kpi-value">{project_total_actual:.1f}h</div>
                </div>
                """, unsafe_allow_html=True)
            with summary_col4:
                status_badge_html = render_status_badge(project_status)
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Status</div>
                    <div style="margin-top: 0.5rem;">{status_badge_html}</div>
                </div>
                """, unsafe_allow_html=True)

            # Create expander with project summary - modern styling
            expander_title = f"📋 Activity Details • {project_activities_count} Items"

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander(expander_title, expanded=True):
                # Configure column display
                column_config = {
                    'Sollstunden': st.column_config.NumberColumn(
                        'Sollstunden (verkauft)',
                        help="Klicken Sie zum Bearbeiten der Sollstunden",
                        min_value=0,
                        max_value=1000,
                        step=0.5,
                        format="%.1f STD"
                    ),
                    'Anteil am Projekt (%)': st.column_config.NumberColumn(
                        'Anteil am Projekt (%)',
                        help="Prozentsatz dieser Tätigkeit am Gesamtprojekt",
                        format="%.1f%%"
                    ),
                    'Erfüllungsstand (%)': st.column_config.NumberColumn(
                        'Erfüllungsstand (%)',
                        help="Automatisch berechnet: Ist/Soll * 100",
                        format="%.1f%%"
                    ),
                    'Iststunden': st.column_config.NumberColumn(
                        'Iststunden',
                        help="Aus Zeiterfassung aggregiert",
                        format="%.1f STD"
                    ),
                    'Status': st.column_config.TextColumn(
                        'Status',
                        help="🟢 ≤100% | 🟡 100-110% | 🔴 >110%"
                    )
                }

                # Show editable dataframe for this project (with fallback for older Streamlit versions)
                try:
                    edited_project_data = st.data_editor(
                        project_df,
                        column_config=column_config,
                        width='stretch',
                        disabled=['Projekt', 'Tätigkeit/Activity', 'Anteil am Projekt (%)', 'Erfüllungsstand (%)', 'Status', 'Iststunden', 'Kunde'],
                        hide_index=True,
                        key=f"editor_{projekt}"
                    )
                except Exception as e:
                    # Fallback for older Streamlit versions
                    st.warning("Verwende vereinfachte Tabellen-Ansicht (ältere Streamlit Version)")
                    st.dataframe(project_df, width='stretch')
                    edited_project_data = project_df  # No editing in fallback mode

                # Process any changes in target hours for this project
                if not edited_project_data.equals(project_df):
                    self.process_target_hour_changes(project_df, edited_project_data)
                    st.rerun()

                # Collect edited data
                all_edited_data.append(edited_project_data)

            # Add visual separator between projects (except after the last one)
            if idx < len(project_list) - 1:
                st.markdown("""
                <div style="margin: 3rem 0; border-bottom: 2px solid #e2e8f0;"></div>
                """, unsafe_allow_html=True)

        # Combine all edited data
        if all_edited_data:
            combined_edited_data = pd.concat(all_edited_data, ignore_index=True)
            return combined_edited_data

        return dashboard_df
    
    def process_target_hour_changes(self, original_df: pd.DataFrame, edited_df: pd.DataFrame):
        """Process changes in target hours"""
        for idx, (_, edited_row) in enumerate(edited_df.iterrows()):
            if idx < len(original_df):
                original_target = original_df.iloc[idx]['Sollstunden']
                edited_target = edited_row['Sollstunden']
                
                if abs(original_target - edited_target) > 0.01:  # Small tolerance for float comparison
                    projekt = edited_row['Projekt']
                    activity = edited_row['Tätigkeit/Activity']
                    
                    # Save to filesystem
                    self.save_target_hours(projekt, activity, edited_target)
                    
                    st.success(f"Sollstunden für '{activity}' in Projekt '{projekt}' auf {edited_target} aktualisiert")
    
    def run(self):
        """Main application run method"""
        
        # Authentication check
        current_user = auth_manager.login_form()
        if not current_user:
            return
        
        # Show user info in sidebar
        auth_manager.show_user_info()
        
        # Main application header with modern design
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 2px solid #e2e8f0;">
            <div style="width: 3rem; height: 3rem; background: linear-gradient(135deg, #135bec 0%, #0d47a1 100%); border-radius: 1rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 6px rgba(19, 91, 236, 0.3);">
                <span class="material-icons" style="color: white; font-size: 1.75rem;">dashboard</span>
            </div>
            <div>
                <h1 style="font-size: 1.875rem; font-weight: 800; color: #0f172a; margin: 0; line-height: 1;">ExecControl</h1>
                <p style="font-size: 0.75rem; color: #64748b; margin: 0; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700;">Project Controlling Dashboard</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Get user permissions and projects
        user_permissions = auth_manager.get_user_permissions(current_user['email'])
        user_projects = user_permissions.get('projects', [])

        # Filter out None values from user projects
        user_projects = [p for p in user_projects if p is not None]

        if not user_projects:
            st.error("Keine Projekte für diesen Benutzer konfiguriert.")
            return
        
        # Sidebar filters with modern design
        with st.sidebar:
            st.markdown("""
            <div style="margin-bottom: 1.5rem;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem;">
                    Main Menu
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="margin-bottom: 1.5rem;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem;">
                    🔍 Filters
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Project selection
            selected_projects = filter_manager.project_filter(user_projects)

            # Filter out None values from selected projects
            selected_projects = [p for p in selected_projects if p is not None]

            if not selected_projects:
                st.warning("Bitte wählen Sie mindestens ein Projekt aus")
                return
            
            # Date filters
            date_filters = filter_manager.date_filter()

            # Load data for filter options
            with st.spinner("Lade Daten..."):
                preview_data = db_config.get_aggregated_data(selected_projects, date_filters, hours_column='FaktStd')

            if preview_data.empty:
                st.info("Keine Daten verfügbar für Filter.")
                selected_employees = []
            else:
                # Employee filter
                selected_employees = filter_manager.employee_filter(preview_data)

            # Additional filters
            search_term = filter_manager.search_filter()
            
            # Hours column selector
            hours_column = filter_manager.hours_column_selector()
            
            # Reset filters button
            if st.button("🔄 Filter zurücksetzen"):
                filter_manager.reset_filters()
            
            # Admin tools with modern design
            if auth_manager.has_permission(current_user['email'], 'admin'):
                st.markdown("""
                <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #e2e8f0;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem;">
                        ⚙️ Admin Tools
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_admin1, col_admin2 = st.columns(2)
                with col_admin1:
                    if st.button("🧹 Cache", use_container_width=True):
                        cache_manager.clear_cache()
                        st.success("✓ Cleared", icon="✅")

                with col_admin2:
                    if st.button("🏥 Health", use_container_width=True):
                        st.session_state.show_health = not st.session_state.get('show_health', False)
        
        # Database connection check
        if not db_config.test_connection():
            st.error("❌ Datenbankverbindung fehlgeschlagen. Bitte prüfen Sie die Konfiguration.")
            st.info("💡 Tipp: Überprüfen Sie die Environment Variables für SQL Server")
            return

        # Set loading state to True before data fetch
        # This ensures skeletons show on every rerun (e.g., when filters change)
        st.session_state.data_loading = True

        # Load data with spinner (wraps ONLY data fetching, not rendering)
        try:
            with st.spinner('Lade Daten...'):
                # Get aggregated time data
                raw_data = db_config.get_aggregated_data(selected_projects, date_filters, hours_column)

                if raw_data.empty:
                    st.info("Keine Daten für die ausgewählten Filter gefunden.")
                    st.session_state.data_loading = False
                    return

                # Customer filter (rendered in sidebar after data is loaded)
                with st.sidebar:
                    selected_customers = filter_manager.customer_filter(raw_data)

                # Apply additional filters
                filter_params = {
                    'search_term': search_term,
                    'selected_customers': selected_customers,
                    'selected_employees': selected_employees,
                }

                filtered_data = filter_manager.apply_filters(raw_data, filter_params)

                # Calculate target_date from date filters for budget calculation
                if 'date_range' in date_filters and date_filters['date_range']:
                    date_range = date_filters['date_range']
                    if len(date_range) == 2 and date_range[1]:
                        target_date_for_budget = date_range[1].isoformat()
                    else:
                        target_date_for_budget = datetime.now().date().isoformat()
                else:
                    target_date_for_budget = datetime.now().date().isoformat()

                # Create dashboard table with time-based budgets
                dashboard_df = self.create_dashboard_table(filtered_data, target_date_for_budget)

                # Create project summary with time-based budgets
                project_summary_df = self.create_project_summary(filtered_data, target_date_for_budget)

                # Mark data as loaded
                st.session_state.data_loading = False

            # Show filter summary
            filter_manager.show_filter_summary({
                **date_filters,
                'selected_projects': selected_projects,
                'selected_customers': selected_customers,
                'selected_employees': selected_employees,
                'search_term': search_term
            }, record_count=len(filtered_data))

            # Calculate target_date from date filters
            # Use the end date from the filter range for budget calculation
            if 'date_range' in date_filters and date_filters['date_range']:
                date_range = date_filters['date_range']
                if len(date_range) == 2 and date_range[1]:
                    target_date = date_range[1].isoformat()
                else:
                    target_date = datetime.now().date().isoformat()
            else:
                target_date = datetime.now().date().isoformat()

            # Tab-Navigation (conditional for admin) - Modern Design
            if auth_manager.has_permission(current_user['email'], 'admin'):
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📊  Dashboard",
                    "📈  Forecast & Timeline",
                    "💰  Budget Management",
                    "📥  Export Data",
                    "⚙️  Administration"
                ])
            else:
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊  Dashboard",
                    "📈  Forecast & Timeline",
                    "💰  Budget Management",
                    "📥  Export Data"
                ])
                tab5 = None

            # Tab 1: Übersicht (Executive Dashboard Style)
            with tab1:
                # Header with project badge
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
                    <div class="project-badge">
                        <span class="material-icons" style="font-size: 1rem; color: #135bec;">folder_open</span>
                        {', '.join(selected_projects[:2])}{'...' if len(selected_projects) > 2 else ''}
                    </div>
                    <h1 style="font-size: 1.5rem; font-weight: 700; color: #0f172a; margin: 0;">Project Controlling Executive Dashboard</h1>
                </div>
                """, unsafe_allow_html=True)

                # KPI Row - 4 Cards
                if not dashboard_df.empty:
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        total_hours = dashboard_df['Iststunden'].sum()
                        render_kpi_card(
                            "Total Hours Logged",
                            f"{total_hours:,.0f}",
                            "schedule",
                            "📊 Across all projects"
                        )

                    with col2:
                        total_target = dashboard_df['Sollstunden'].sum()
                        budget_consumption = (total_hours / total_target * 100) if total_target > 0 else 0
                        render_kpi_card(
                            "Budget Consumption",
                            f"{budget_consumption:.1f}%",
                            "payments",
                            f"Target: {total_target:.0f}h"
                        )

                    with col3:
                        active_projects = dashboard_df['Projekt'].nunique()
                        nearing_completion = len(dashboard_df[dashboard_df['Erfüllungsstand (%)'] >= 90])
                        render_kpi_card(
                            "Active Projects",
                            f"{active_projects}",
                            "folder",
                            f"{nearing_completion} nearing completion" if nearing_completion > 0 else "All on track"
                        )

                    with col4:
                        overbooked = len(dashboard_df[dashboard_df['Status'] == '🔴 Überbucht'])
                        render_kpi_card(
                            "Critical Activities",
                            f"{overbooked}",
                            "warning" if overbooked > 0 else "check_circle",
                            "Need attention" if overbooked > 0 else "All healthy",
                            "negative" if overbooked > 0 else "positive"
                        )

                st.markdown("<br>", unsafe_allow_html=True)

                # Two-column layout: Chart + Project Health
                col_chart, col_health = st.columns([2, 1])

                with col_chart:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    render_section_header("Planned vs. Actual Hours", "Comparison across all projects")

                    if not project_summary_df.empty:
                        # Create horizontal bar chart data
                        chart_data = project_summary_df.head(5).copy()
                        chart_data['Planned'] = chart_data['Sollstunden Gesamt']
                        chart_data['Actual'] = chart_data['Iststunden Gesamt']

                        # Display bars
                        for idx, row in chart_data.iterrows():
                            st.markdown(f"""
                            <div style="margin-bottom: 1.5rem;">
                                <div style="display: flex; justify-content: space-between; font-size: 0.875rem; font-weight: 600; margin-bottom: 0.5rem;">
                                    <span>{row['Projekt']}</span>
                                    <span style="color: #64748b;">{row['Actual']:.0f} / {row['Planned']:.0f} hrs</span>
                                </div>
                                <div style="position: relative; height: 1.5rem; background: #f1f5f9; border-radius: 0.5rem; overflow: hidden;">
                                    <div style="position: absolute; top: 0; left: 0; height: 100%; background: #cbd5e1; width: {min(row['Planned']/chart_data['Planned'].max()*100, 100)}%;"></div>
                                    <div style="position: absolute; top: 0; left: 0; height: 100%; background: #135bec; width: {min(row['Actual']/chart_data['Planned'].max()*100, 100)}%;"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Legend
                        st.markdown("""
                        <div style="display: flex; gap: 1.5rem; margin-top: 1.5rem;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="width: 0.75rem; height: 0.75rem; background: #cbd5e1; border-radius: 0.125rem;"></span>
                                <span style="font-size: 0.75rem; color: #64748b;">Planned</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="width: 0.75rem; height: 0.75rem; background: #135bec; border-radius: 0.125rem;"></span>
                                <span style="font-size: 0.75rem; color: #64748b;">Actual</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

                with col_health:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    render_section_header("Project Health", "Portfolio Status Overview")

                    if not project_summary_df.empty:
                        # Create health table
                        st.markdown("""
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #f8fafc; font-size: 0.75rem; color: #64748b; text-transform: uppercase;">
                                    <th style="padding: 0.75rem; text-align: left; font-weight: 700;">Project</th>
                                    <th style="padding: 0.75rem; text-align: left; font-weight: 700;">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                        """, unsafe_allow_html=True)

                        for idx, row in project_summary_df.iterrows():
                            project_name = row['Projekt'][:20] + "..." if len(row['Projekt']) > 20 else row['Projekt']
                            kunde = row['Kunde'][:15] + "..." if len(row['Kunde']) > 15 else row['Kunde']
                            budget_pct = row['Erfüllungsstand (%)']
                            status_html = render_status_badge(row['Status'])

                            st.markdown(f"""
                            <tr style="border-bottom: 1px solid #f1f5f9;">
                                <td style="padding: 1rem; font-size: 0.875rem;">
                                    <div style="font-weight: 600;">{project_name}</div>
                                    <div style="font-size: 0.625rem; color: #94a3b8;">{kunde}</div>
                                </td>
                                <td style="padding: 1rem;">
                                    {status_html}
                                    <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;">{budget_pct:.0f}%</div>
                                </td>
                            </tr>
                            """, unsafe_allow_html=True)

                        st.markdown("</tbody></table>", unsafe_allow_html=True)

                        st.markdown("""
                        <div style="text-align: center; padding: 1rem; border-top: 1px solid #e2e8f0;">
                            <a href="#" style="color: #135bec; font-size: 0.875rem; font-weight: 600; text-decoration: none;">View All Projects →</a>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

                # Budget calculation info
                budget_date_obj = datetime.fromisoformat(target_date_for_budget).date()
                st.info(f"""
                💡 **Budget-Berechnung:** Die angezeigten Sollstunden gelten für den Stichtag **{budget_date_obj.strftime('%d.%m.%Y')}**.
                Budgetänderungen, die nach diesem Datum erfasst wurden, werden nicht berücksichtigt.
                """)

                st.markdown("<br>", unsafe_allow_html=True)

                # Show main dashboard (detailed view)
                render_section_header("Detailed Activity View", "Edit target hours and track progress per activity")
                final_dashboard = self.show_editable_dashboard(dashboard_df)

            # Tab 2: Zeitreihen & Prognosen (Forecast Dashboard Style)
            with tab2:
                # Header
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
                    <div class="project-badge">
                        <span class="material-icons" style="font-size: 1rem; color: #135bec;">insights</span>
                        Forecast Analysis
                    </div>
                    <h1 style="font-size: 1.5rem; font-weight: 700; color: #0f172a; margin: 0;">Project Budget & Forecast Dashboard</h1>
                </div>
                """, unsafe_allow_html=True)

                # KPI Cards Row - 3 Cards
                if not dashboard_df.empty:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        total_target = dashboard_df['Sollstunden'].sum()
                        render_kpi_card(
                            "Total Budget",
                            f"{total_target:,.0f} STD",
                            "payments",
                            "Inclusive of all extensions",
                            "neutral"
                        )

                    with col2:
                        total_hours = dashboard_df['Iststunden'].sum()
                        consumption_rate = (total_hours / total_target * 100) if total_target > 0 else 0
                        render_kpi_card(
                            "Spent Hours",
                            f"{total_hours:,.0f}",
                            "schedule",
                            f"{consumption_rate:.1f}% Consumption Rate",
                            "neutral"
                        )

                    with col3:
                        remaining = total_target - total_hours
                        render_kpi_card(
                            "Remaining Budget",
                            f"{remaining:,.0f} STD",
                            "hourglass_empty",
                            f"{(remaining/total_target*100):.0f}% available" if total_target > 0 else "N/A",
                            "positive" if remaining > 0 else "negative"
                        )

                st.markdown("<br>", unsafe_allow_html=True)

                # Level-Auswahl
                st.markdown("""
                <div style="margin-bottom: 1.5rem;">
                    <label style="font-size: 0.875rem; font-weight: 600; color: #64748b;">Analysis Level</label>
                </div>
                """, unsafe_allow_html=True)

                analysis_level = st.radio(
                    "",
                    ["Projekt-Übersicht", "Nach Activity"],
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                if analysis_level == "Projekt-Übersicht":
                    # Für jedes Projekt: Forecast-Szenarien + Sprint-Analyse
                    for projekt in selected_projects:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #135bec 0%, #0d47a1 100%); padding: 1rem 1.5rem; border-radius: 1rem; margin: 2rem 0 1.5rem 0; box-shadow: 0 4px 6px rgba(19, 91, 236, 0.2);">
                            <div style="display: flex; align-items: center; gap: 0.75rem;">
                                <span class="material-icons" style="color: white; font-size: 1.5rem;">folder_open</span>
                                <h3 style="color: white; font-size: 1.25rem; font-weight: 700; margin: 0;">Projekt: {projekt}</h3>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        try:
                            # Daten laden
                            project_bookings = db_config.get_project_bookings([projekt], hours_column, filters=date_filters)

                            if project_bookings.empty:
                                st.info(f"Keine Buchungsdaten für Projekt '{projekt}' verfügbar")
                                continue

                            # Target Hours berechnen
                            all_targets = self.load_target_hours()
                            project_targets = all_targets.get(projekt, {})
                            total_target = sum(project_targets.values()) if project_targets else 0

                            # NEU: Forecast-Szenarien (ersetzt alten Burndown)
                            active_hours = render_forecast_scenarios(
                                project_id=projekt,
                                bookings_df=project_bookings,
                                target_hours=total_target,
                                user_email=current_user.get('email', 'unknown'),
                                activity=None
                            )

                            st.divider()

                            # NEU: Szenario-Chart (mit aktivem Wert aus UI)
                            key_suffix = f"{projekt}"
                            use_manual = st.session_state.get(f"mf_use_{key_suffix}", False)

                            render_scenario_chart(
                                project_id=projekt,
                                bookings_df=project_bookings,
                                target_hours=total_target,
                                activity=None,
                                manual_hours_per_sprint=active_hours,
                                use_manual=use_manual
                            )

                            # NEU: Sprint-Velocity Chart (optional)
                            with st.expander("📊 Sprint-Velocity Analyse"):
                                engine = ForecastEngine(project_bookings, total_target)
                                if len(engine.sprint_data) > 0:
                                    render_sprint_velocity_chart(engine.sprint_data)
                                else:
                                    st.info("Keine Sprint-Daten verfügbar (benötigt Buchungen der letzten 8 Wochen)")

                            # Bestehender Wochentrend (optional in Expander)
                            with st.expander("📊 Wochentrend anzeigen"):
                                render_weekly_trend(project_bookings, projekt)

                            st.markdown("---")

                        except Exception as e:
                            st.error(f"Fehler beim Laden der Zeitreihen für Projekt '{projekt}': {str(e)}")

                else:  # Nach Activity
                    # Activity-Level Charts für jedes Projekt
                    for projekt in selected_projects:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #135bec 0%, #0d47a1 100%); padding: 1rem 1.5rem; border-radius: 1rem; margin: 2rem 0 1.5rem 0; box-shadow: 0 4px 6px rgba(19, 91, 236, 0.2);">
                            <div style="display: flex; align-items: center; gap: 0.75rem;">
                                <span class="material-icons" style="color: white; font-size: 1.5rem;">folder_open</span>
                                <h3 style="color: white; font-size: 1.25rem; font-weight: 700; margin: 0;">Projekt: {projekt}</h3>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        try:
                            # Daten laden
                            project_bookings = db_config.get_project_bookings([projekt], hours_column, filters=date_filters)

                            if project_bookings.empty:
                                st.info(f"Keine Buchungsdaten für Projekt '{projekt}' verfügbar")
                                continue

                            # Target Hours pro Activity
                            all_targets = self.load_target_hours()
                            project_targets = all_targets.get(projekt, {})

                            # Activity-spezifische Forecast-Szenarien
                            if 'Activity' in project_bookings.columns:
                                for activity in project_bookings['Activity'].unique():
                                    st.markdown(f"""
                                    <div style="background: white; padding: 0.75rem 1rem; border-radius: 0.5rem; margin: 1.5rem 0 1rem 0; border-left: 4px solid #135bec; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                                            <span class="material-icons" style="color: #135bec; font-size: 1.25rem;">assignment</span>
                                            <h4 style="color: #0f172a; font-size: 1rem; font-weight: 600; margin: 0;">Activity: {activity}</h4>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                    activity_bookings = project_bookings[project_bookings['Activity'] == activity]
                                    activity_target = project_targets.get(activity, 0.0)

                                    # Forecast-Szenarien für diese Activity
                                    activity_active_hours = render_forecast_scenarios(
                                        project_id=projekt,
                                        bookings_df=activity_bookings,
                                        target_hours=activity_target,
                                        user_email=current_user.get('email', 'unknown'),
                                        activity=activity
                                    )

                                    # Szenario-Chart (mit aktivem Wert aus UI)
                                    with st.expander("📊 Szenario-Visualisierung"):
                                        key_suffix_act = f"{projekt}_{activity}"
                                        use_manual_act = st.session_state.get(f"mf_use_{key_suffix_act}", False)

                                        render_scenario_chart(
                                            project_id=projekt,
                                            bookings_df=activity_bookings,
                                            target_hours=activity_target,
                                            activity=activity,
                                            manual_hours_per_sprint=activity_active_hours,
                                            use_manual=use_manual_act
                                        )
                                    
                                    st.markdown("---")
                                
                                # Bestehende Activity Comparison als Übersicht
                                with st.expander("📊 Activity-Vergleich anzeigen"):
                                    render_activity_comparison(project_bookings, projekt)
                                    render_cumulative_comparison(project_bookings, project_targets)
                            else:
                                st.warning("Activity-Spalte nicht verfügbar")
                            
                            st.markdown("---")
                            
                        except Exception as e:
                            st.error(f"Fehler beim Laden der Activity-Charts für Projekt '{projekt}': {str(e)}")
            
            # Tab 3: Budget-Verwaltung (Budget Management Style)
            with tab3:
                # Header with summary cards
                st.markdown("""
                <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2rem; gap: 2rem;">
                    <div>
                        <h1 style="font-size: 2rem; font-weight: 700; color: #0f172a; margin: 0;">Budget Management</h1>
                        <p style="color: #64748b; margin-top: 0.5rem;">Monitor and adjust the financial scope for your projects</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Summary cards
                if not dashboard_df.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        total_target = dashboard_df['Sollstunden'].sum()
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-label">Total Budget Hours</div>
                            <div class="kpi-value" style="color: #135bec;">{total_target:,.1f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        total_activities = len(dashboard_df)
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-label">Total Activities</div>
                            <div class="kpi-value" style="color: #135bec;">{total_activities}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Budget management component (wrapped in styled container)
                st.markdown('<div style="background: white; border-radius: 1rem; padding: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0;">', unsafe_allow_html=True)
                budget_manager.show_budget_management(
                    user_email=current_user['email'],
                    user_projects=user_projects
                )
                st.markdown('</div>', unsafe_allow_html=True)

            # Tab 4: Export (Modern Design)
            with tab4:
                # Header
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
                    <div class="project-badge">
                        <span class="material-icons" style="font-size: 1rem; color: #135bec;">download</span>
                        Data Export
                    </div>
                    <h1 style="font-size: 1.5rem; font-weight: 700; color: #0f172a; margin: 0;">Export Dashboard Data</h1>
                </div>
                """, unsafe_allow_html=True)

                # Export functionality
                if auth_manager.has_permission(current_user['email'], 'export'):
                    # Export info cards
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-card-icon">
                                <span class="material-icons" style="color: #135bec; font-size: 1.5rem;">table_chart</span>
                            </div>
                            <div class="kpi-label">Records Ready</div>
                            <div class="kpi-value">{len(filtered_data) if not filtered_data.empty else 0}</div>
                            <div class="kpi-trend neutral">Available for export</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-card-icon">
                                <span class="material-icons" style="color: #135bec; font-size: 1.5rem;">folder</span>
                            </div>
                            <div class="kpi-label">Projects</div>
                            <div class="kpi-value">{len(selected_projects)}</div>
                            <div class="kpi-trend neutral">Selected projects</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        date_range_text = "All time"
                        if 'date_range' in date_filters and date_filters['date_range']:
                            dr = date_filters['date_range']
                            if len(dr) == 2 and dr[0] and dr[1]:
                                date_range_text = f"{dr[0].strftime('%d.%m.%y')} - {dr[1].strftime('%d.%m.%y')}"

                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-card-icon">
                                <span class="material-icons" style="color: #135bec; font-size: 1.5rem;">date_range</span>
                            </div>
                            <div class="kpi-label">Date Range</div>
                            <div class="kpi-value" style="font-size: 1.25rem;">{date_range_text}</div>
                            <div class="kpi-trend neutral">Filter applied</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Export options in styled container
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    render_section_header("Export Options", "Download your data in various formats")

                    excel_exporter.show_export_options(
                        dashboard_df,
                        filtered_data,
                        current_user,
                        {
                            'selected_projects': selected_projects,
                            **date_filters
                        }
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="kpi-card" style="background: #fef3c7; border-color: #fbbf24;">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <span class="material-icons" style="color: #92400e; font-size: 2rem;">lock</span>
                            <div>
                                <div style="font-weight: 700; color: #92400e; font-size: 1.125rem;">Access Restricted</div>
                                <div style="color: #92400e; margin-top: 0.5rem;">Sie haben keine Berechtigung zum Export von Daten</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Tab 5: Administration (nur für Admins) - Modern Design
            if tab5 is not None:
                with tab5:
                    # Header
                    st.markdown("""
                    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
                        <div class="project-badge">
                            <span class="material-icons" style="font-size: 1rem; color: #135bec;">admin_panel_settings</span>
                            Admin Panel
                        </div>
                        <h1 style="font-size: 1.5rem; font-weight: 700; color: #0f172a; margin: 0;">User Management & Administration</h1>
                    </div>
                    """, unsafe_allow_html=True)

                    # Admin info cards
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("""
                        <div class="kpi-card">
                            <div class="kpi-card-icon">
                                <span class="material-icons" style="color: #135bec; font-size: 1.5rem;">people</span>
                            </div>
                            <div class="kpi-label">System Users</div>
                            <div class="kpi-value">Active</div>
                            <div class="kpi-trend neutral">User management</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown("""
                        <div class="kpi-card">
                            <div class="kpi-card-icon">
                                <span class="material-icons" style="color: #135bec; font-size: 1.5rem;">security</span>
                            </div>
                            <div class="kpi-label">Permissions</div>
                            <div class="kpi-value">Role-based</div>
                            <div class="kpi-trend neutral">Access control</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        st.markdown("""
                        <div class="kpi-card">
                            <div class="kpi-card-icon">
                                <span class="material-icons" style="color: #135bec; font-size: 1.5rem;">settings</span>
                            </div>
                            <div class="kpi-label">System Status</div>
                            <div class="kpi-value">Healthy</div>
                            <div class="kpi-trend positive">All systems operational</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # User management in styled container
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    render_section_header("User Management", "Manage user access and permissions")
                    admin_user_manager.show_user_management()
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Show health check if requested
            if st.session_state.get('show_health', False):
                health_checker.show_health_dashboard()
            
        except Exception as e:
            st.session_state.data_loading = False
            st.error(f"Fehler beim Laden der Daten: {str(e)}")
            st.info("Bitte versuchen Sie es später erneut oder wenden Sie sich an den Administrator.")

# Health check endpoint (for Docker health checks)
def health_endpoint():
    """Simple health check endpoint"""
    try:
        health_data = health_checker.run_all_checks()
        return health_data['overall_status'] in ['healthy', 'degraded']
    except:
        return False

# Initialize and run application
if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("cache", exist_ok=True)
    
    # Initialize app
    app = TimeTrackingApp()
    app.run()
