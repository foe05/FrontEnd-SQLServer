"""
Main Streamlit application for SQL Server Dashboard
"""
import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Page configuration MUST be first Streamlit command
st.set_page_config(
    page_title="SQL Server Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import custom components AFTER page config
from components.auth import auth_manager
from components.filters import filter_manager
from components.export import excel_exporter
from components.admin_user_manager import admin_user_manager
from components.skeleton_loaders import show_table_skeleton
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
    st.sidebar.success("🧪 TEST-MODUS AKTIV")
else:
    from config.database import db_config

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
        st.subheader("📊 Projekt Dashboard")

        # Check if data is still loading
        if st.session_state.get('data_loading', False):
            # Show skeleton while data is loading
            st.markdown("### Detailansicht")
            show_table_skeleton(num_rows=10, num_columns=8)
            return pd.DataFrame()

        if dashboard_df.empty:
            st.warning("Keine Daten verfügbar für die ausgewählten Filter")
            return dashboard_df

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
        
        # Show editable dataframe (with fallback for older Streamlit versions)
        try:
            edited_data = st.data_editor(
                edited_df,
                column_config=column_config,
                width='stretch',
                disabled=['Projekt', 'Tätigkeit/Activity', 'Anteil am Projekt (%)', 'Erfüllungsstand (%)', 'Status', 'Iststunden', 'Kunde']
            )
        except Exception as e:
            # Fallback for older Streamlit versions
            st.warning("Verwende vereinfachte Tabellen-Ansicht (ältere Streamlit Version)")
            st.dataframe(edited_df, width='stretch')
            edited_data = edited_df  # No editing in fallback mode
        
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

                # Apply additional filters
                filter_params = {
                    'search_term': search_term,
                }

                filtered_data = filter_manager.apply_filters(raw_data, filter_params)

                # Create dashboard table
                dashboard_df = self.create_dashboard_table(filtered_data)

                # Create project summary
                project_summary_df = self.create_project_summary(filtered_data)

                # Mark data as loaded
                st.session_state.data_loading = False

            # Show filter summary
            filter_manager.show_filter_summary({
                **date_filters,
                'selected_projects': selected_projects,
                'search_term': search_term
            })

            # Tab-Navigation (conditional for admin)
            if auth_manager.has_permission(current_user['email'], 'admin'):
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Übersicht", "📈 Zeitreihen", "📥 Export", "⚙️ Administration"])
            else:
                tab1, tab2, tab3 = st.tabs(["📊 Übersicht", "📈 Zeitreihen", "📥 Export"])
                tab4 = None

            # Tab 1: Übersicht (bestehende Funktionalität)
            with tab1:
                # Show project summary first
                st.subheader("📊 Projekt-Zusammenfassung")
                st.markdown("Übersicht über Soll- vs. Ist-Stunden pro Projekt")

                if st.session_state.get('data_loading', False):
                    # Show skeleton while data is loading
                    show_table_skeleton(num_rows=len(selected_projects), num_columns=7)
                elif not project_summary_df.empty:
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
                        width='stretch'
                    )

                st.markdown("---")  # Separator

                # Show main dashboard
                final_dashboard = self.show_editable_dashboard(dashboard_df)

            # Tab 2: Zeitreihen & Prognosen
            with tab2:
                st.header("📈 Zeitreihen & Prognosen")
                
                # Level-Auswahl
                analysis_level = st.radio(
                    "Analyse-Ebene:", 
                    ["Projekt-Übersicht", "Nach Activity"], 
                    horizontal=True
                )
                
                if analysis_level == "Projekt-Übersicht":
                    # Für jedes Projekt: Forecast-Szenarien + Sprint-Analyse
                    for projekt in selected_projects:
                        st.markdown(f"### 📂 Projekt: {projekt}")
                        
                        try:
                            # Daten laden
                            project_bookings = db_config.get_project_bookings([projekt], hours_column)
                            
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
                        st.markdown(f"### 📂 Projekt: {projekt}")
                        
                        try:
                            # Daten laden
                            project_bookings = db_config.get_project_bookings([projekt], hours_column)
                            
                            if project_bookings.empty:
                                st.info(f"Keine Buchungsdaten für Projekt '{projekt}' verfügbar")
                                continue
                            
                            # Target Hours pro Activity
                            all_targets = self.load_target_hours()
                            project_targets = all_targets.get(projekt, {})
                            
                            # Activity-spezifische Forecast-Szenarien
                            if 'Activity' in project_bookings.columns:
                                for activity in project_bookings['Activity'].unique():
                                    st.markdown(f"#### 📋 Activity: {activity}")
                                    
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
            
            # Tab 3: Export
            with tab3:
                st.header("📥 Export")
                
                # Export functionality
                if auth_manager.has_permission(current_user['email'], 'export'):
                    excel_exporter.show_export_options(
                        dashboard_df,
                        filtered_data,
                        current_user,
                        {
                            'selected_projects': selected_projects,
                            **date_filters
                        }
                    )
                else:
                    st.warning("Sie haben keine Berechtigung zum Export von Daten")
            
            # Tab 4: Administration (nur für Admins)
            if tab4 is not None:
                with tab4:
                    admin_user_manager.show_user_management()
            
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
