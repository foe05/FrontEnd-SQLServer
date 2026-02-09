"""
Filter components for project and data filtering
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime, date

class FilterManager:
    """Manage filters for time entries and project data"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        
    def project_filter(self, available_projects: List[str]) -> List[str]:
        """Project selection filter"""
        if not available_projects:
            st.warning("Keine Projekte verfügbar für diesen Benutzer")
            return []
        
        # Initialize session state
        if 'selected_projects' not in st.session_state:
            st.session_state.selected_projects = available_projects[:1] if available_projects else []
        
        selected = st.multiselect(
            "🏗️ Projekte auswählen",
            options=available_projects,
            default=st.session_state.selected_projects,
            help="Wählen Sie ein oder mehrere Projekte aus"
        )
        
        st.session_state.selected_projects = selected
        return selected
    
    def date_filter(self) -> Dict[str, Any]:
        """Date range and period filters"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            year = st.selectbox(
                "📅 Jahr",
                options=list(range(self.current_year - 2, self.current_year + 1)),
                index=2,  # Current year
                help="Wählen Sie das Jahr für die Auswertung"
            )
        
        with col2:
            month = st.selectbox(
                "📅 Monat",
                options=["Alle"] + [f"{i:02d}" for i in range(1, 13)],
                index=0,
                help="Wählen Sie einen spezifischen Monat oder 'Alle'"
            )
        
        with col3:
            quarter = st.selectbox(
                "📅 Quartal",
                options=["Alle", "Q1", "Q2", "Q3", "Q4"],
                index=0,
                help="Wählen Sie ein Quartal"
            )
        
        # Convert filters to database format
        filters = {"year": year}
        
        if month != "Alle":
            filters["month"] = int(month)
        
        if quarter != "Alle":
            quarter_months = {
                "Q1": [1, 2, 3],
                "Q2": [4, 5, 6], 
                "Q3": [7, 8, 9],
                "Q4": [10, 11, 12]
            }
            if month == "Alle":  # Only apply quarter if no specific month selected
                filters["quarter_months"] = quarter_months[quarter]
        
        return filters
    
    def status_filter(self) -> List[str]:
        """Status filter for time entries"""
        status_options = ["Alle", "Genehmigt", "Offen", "Abgelehnt", "Entwurf"]
        
        selected_statuses = st.multiselect(
            "📊 Status Filter",
            options=status_options,
            default=["Alle"],
            help="Filtern Sie nach Buchungsstatus"
        )
        
        if "Alle" in selected_statuses:
            return []
        else:
            return selected_statuses
    
    def activity_filter(self, df: pd.DataFrame) -> List[str]:
        """Filter by activity/usage (Verwendung)"""
        if df.empty:
            return []
        
        activities = sorted(df['Activity'].unique()) if 'Activity' in df.columns else []
        
        if not activities:
            return []
        
        selected_activities = st.multiselect(
            "🎯 Tätigkeiten Filter",
            options=["Alle"] + activities,
            default=["Alle"],
            help="Filtern Sie nach spezifischen Tätigkeiten"
        )
        
        if "Alle" in selected_activities:
            return activities
        else:
            return selected_activities
    
    def search_filter(self) -> str:
        """Text search filter"""
        search_term = st.text_input(
            "🔍 Suche",
            placeholder="Suchen Sie in Projektnamen, Tätigkeiten oder Kommentaren...",
            help="Textsuche in verschiedenen Feldern"
        )
        return search_term.strip()
    
    def hours_column_selector(self) -> str:
        """Select which column to use for actual hours"""
        hours_column = st.selectbox(
            "⏱️ Stunden-Quelle",
            options=["FaktStd", "Zeit"],
            index=0,  # FaktStd as default
            help="Wählen Sie welche Spalte für Iststunden verwendet werden soll"
        )
        return hours_column
    
    def apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply all filters to DataFrame"""
        if df.empty:
            return df
        
        filtered_df = df.copy()
        
        # Apply activity filter
        if 'selected_activities' in filters and filters['selected_activities']:
            if 'Activity' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['Activity'].isin(filters['selected_activities'])]
        
        # Apply search filter
        if 'search_term' in filters and filters['search_term']:
            search_cols = ['Activity', 'Projekt', 'Kundenname']
            search_cols = [col for col in search_cols if col in filtered_df.columns]
            
            if search_cols:
                mask = pd.Series([False] * len(filtered_df))
                for col in search_cols:
                    mask = mask | filtered_df[col].str.contains(
                        filters['search_term'], 
                        case=False, 
                        na=False
                    )
                filtered_df = filtered_df[mask]
        
        return filtered_df
    
    def show_filter_summary(self, filters: Dict[str, Any]):
        """Show applied filters summary"""
        active_filters = []

        if 'year' in filters:
            active_filters.append(f"Jahr: {filters['year']}")

        if 'month' in filters:
            active_filters.append(f"Monat: {filters['month']:02d}")

        if 'quarter_months' in filters:
            quarters = {
                str([1,2,3]): "Q1",
                str([4,5,6]): "Q2",
                str([7,8,9]): "Q3",
                str([10,11,12]): "Q4"
            }
            quarter_key = str(filters['quarter_months'])
            if quarter_key in quarters:
                active_filters.append(f"Quartal: {quarters[quarter_key]}")

        if 'selected_activities' in filters and filters['selected_activities']:
            if len(filters['selected_activities']) <= 3:
                active_filters.append(f"Tätigkeiten: {', '.join(filters['selected_activities'])}")
            else:
                active_filters.append(f"Tätigkeiten: {len(filters['selected_activities'])} ausgewählt")

        if 'search_term' in filters and filters['search_term']:
            active_filters.append(f"Suche: '{filters['search_term']}'")

        if active_filters:
            # Display prominent filter count badge
            col1, col2 = st.columns([1, 4])

            with col1:
                st.metric("🔍 Aktive Filter", len(active_filters))

            with col2:
                st.info("**Filter Details:** " + " | ".join(active_filters))
        
    def reset_filters(self):
        """Reset all filters to default"""
        filter_keys = [
            'selected_projects',
            'selected_activities', 
            'search_term'
        ]
        
        for key in filter_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        st.rerun()

# Global filter manager instance
filter_manager = FilterManager()
