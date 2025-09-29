"""
Main Streamlit application for SQL Server Dashboard
"""
import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Import custom components
from components.auth import auth_manager
from components.filters import filter_manager
from components.export import excel_exporter
from utils.cache import cache_manager
from utils.health import health_checker

# Import database config based on environment
if os.getenv('TEST_MODE', 'false').lower() == 'true':
    from config.test_database import test_db_config as db_config
    st.sidebar.success("🧪 TEST-MODUS AKTIV")
else:
    from config.database import db_config

# Page configuration
st.set_page_config(
    page_title="SQL Server Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class TimeTrackingApp:
    """Main application class"""
    
    def __init__(self):
        self.target_hours_file = "cache/target_hours.json"
        
    def load_target_hours(self) -> Dict[str, Dict[str, float]]:
        """Load target hours from filesystem"""
        return cache_manager.load_all_target_hours()
    
    def save_target_hours(self, project: str, activity: str, target_hours: float):
        """Save target hours to filesystem"""
        cache_manager.save_target_hours(project, activity, target_hours)
    
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
    
    def create_dashboard_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create the main dashboard table with editable target hours"""
        if df.empty:
            return pd.DataFrame()
        
        # Load existing target hours
        all_targets = self.load_target_hours()
        
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
    
    def create_project_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create project summary with total target vs actual hours"""
        if df.empty:
            return pd.DataFrame()
        
        # Load existing target hours
        all_targets = self.load_target_hours()
        
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
        """Show the main dashboard with editable target hours"""
        if dashboard_df.empty:
            st.warning("Keine Daten verfügbar für die ausgewählten Filter")
            return dashboard_df
        
        st.subheader("📊 Projekt Dashboard")
        
        # Display metrics summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_projects = dashboard_df['Projekt'].nunique()
            st.metric("Projekte", total_projects)
        
        with col2:
            total_activities = len(dashboard_df)
            st.metric("Tätigkeiten", total_activities)
        
        with col3:
            total_actual = dashboard_df['Iststunden'].sum()
            st.metric("Iststunden Gesamt", f"{total_actual:.1f}")
        
        with col4:
            overbooked = len(dashboard_df[dashboard_df['Status'] == '🔴 Überbucht'])
            st.metric("Überbuchte Tätigkeiten", overbooked)
        
        # Show table with editing capabilities
        st.markdown("### Detailansicht")
        
        # Create a copy for editing
        edited_df = dashboard_df.copy()
        
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
        
        # Show editable dataframe
        edited_data = st.data_editor(
            edited_df,
            column_config=column_config,
            use_container_width=True,
            key="dashboard_editor",
            disabled=['Projekt', 'Tätigkeit/Activity', 'Anteil am Projekt (%)', 'Erfüllungsstand (%)', 'Status', 'Iststunden', 'Kunde']
        )
        
        # Process any changes in target hours
        if not edited_data.equals(edited_df):
            self.process_target_hour_changes(edited_df, edited_data)
            st.rerun()
        
        return edited_data
    
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
        
        # Main application
        st.title("📊 SQL Server Dashboard - Zeiterfassung")
        
        # Get user permissions and projects
        user_permissions = auth_manager.get_user_permissions(current_user['email'])
        user_projects = user_permissions.get('projects', [])
        
        if not user_projects:
            st.error("Keine Projekte für diesen Benutzer konfiguriert.")
            return
        
        # Sidebar filters
        with st.sidebar:
            st.markdown("### 🔍 Filter")
            
            # Project selection
            selected_projects = filter_manager.project_filter(user_projects)
            
            if not selected_projects:
                st.warning("Bitte wählen Sie mindestens ein Projekt aus")
                return
            
            # Date filters
            date_filters = filter_manager.date_filter()
            
            # Additional filters
            search_term = filter_manager.search_filter()
            
            # Hours column selector
            hours_column = filter_manager.hours_column_selector()
            
            # Reset filters button
            if st.button("🔄 Filter zurücksetzen"):
                filter_manager.reset_filters()
            
            # Admin tools
            if auth_manager.has_permission(current_user['email'], 'admin'):
                st.markdown("### ⚙️ Admin Tools")
                if st.button("🧹 Cache leeren"):
                    cache_manager.clear_cache()
                    st.success("Cache geleert")
                
                if st.button("🏥 Health Check"):
                    st.session_state.show_health = not st.session_state.get('show_health', False)
        
        # Database connection check
        if not db_config.test_connection():
            st.error("❌ Datenbankverbindung fehlgeschlagen. Bitte prüfen Sie die Konfiguration.")
            st.info("💡 Tipp: Überprüfen Sie die Environment Variables für SQL Server")
            return
        
        # Load data
        try:
            with st.spinner("Lade Daten..."):
                # Get aggregated time data
                raw_data = db_config.get_aggregated_data(selected_projects, date_filters, hours_column)
                
                if raw_data.empty:
                    st.info("Keine Daten für die ausgewählten Filter gefunden.")
                    return
                
                # Apply additional filters
                filter_params = {
                    'search_term': search_term,
                }
                
                filtered_data = filter_manager.apply_filters(raw_data, filter_params)
                
                # Create dashboard table
                dashboard_df = self.create_dashboard_table(filtered_data)
                
                # Create project summary
                project_summary_df = self.create_project_summary(filtered_data)
                
                # Show filter summary
                filter_manager.show_filter_summary({
                    **date_filters,
                    'selected_projects': selected_projects,
                    'search_term': search_term
                })
                
                # Show project summary first
                if not project_summary_df.empty:
                    st.subheader("📊 Projekt-Zusammenfassung")
                    st.markdown("Übersicht über Soll- vs. Ist-Stunden pro Projekt")
                    
                    # Configure project summary columns
                    project_summary_config = {
                        'Sollstunden Gesamt': st.column_config.NumberColumn(
                            'Sollstunden Gesamt',
                            help="Summe aller verkauften Stunden für dieses Projekt",
                            format="%.1f STD"
                        ),
                        'Iststunden Gesamt': st.column_config.NumberColumn(
                            'Iststunden Gesamt',
                            help="Summe aller gebuchten Stunden für dieses Projekt",
                            format="%.1f STD"
                        ),
                        'Erfüllungsstand (%)': st.column_config.NumberColumn(
                            'Erfüllungsstand (%)',
                            help="Gesamterfüllungsstand des Projekts",
                            format="%.1f%%"
                        ),
                        'Status': st.column_config.TextColumn(
                            'Status',
                            help="🟢 ≤100% | 🟡 100-110% | 🔴 >110%"
                        )
                    }
                    
                    st.dataframe(
                        project_summary_df,
                        column_config=project_summary_config,
                        use_container_width=True,
                        key="project_summary"
                    )
                
                st.markdown("---")  # Separator
                
                # Show main dashboard
                final_dashboard = self.show_editable_dashboard(dashboard_df)
                
                # Export functionality
                if auth_manager.has_permission(current_user['email'], 'export'):
                    excel_exporter.show_export_options(
                        final_dashboard,
                        filtered_data,
                        current_user,
                        {
                            'selected_projects': selected_projects,
                            **date_filters
                        }
                    )
                
                # Show health check if requested
                if st.session_state.get('show_health', False):
                    health_checker.show_health_dashboard()
                
        except Exception as e:
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
