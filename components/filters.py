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
        """Project selection filter using checkboxes"""
        if not available_projects:
            st.warning("Keine Projekte verfügbar für diesen Benutzer")
            return []

        st.markdown("**🏗️ Projekte auswählen**")

        # Initialize session state for each project checkbox
        for proj in available_projects:
            key = f"proj_{proj}"
            if key not in st.session_state:
                # Default: first project selected
                st.session_state[key] = (proj == available_projects[0])

        # Select all / deselect all toggle
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Alle", key="select_all_projects", use_container_width=True):
                for proj in available_projects:
                    st.session_state[f"proj_{proj}"] = True
                st.rerun()
        with col2:
            if st.button("Keine", key="deselect_all_projects", use_container_width=True):
                for proj in available_projects:
                    st.session_state[f"proj_{proj}"] = False
                st.rerun()

        # Render a checkbox for each project
        selected = []
        for proj in available_projects:
            if st.checkbox(proj, key=f"proj_{proj}"):
                selected.append(proj)

        st.session_state.selected_projects = selected
        return selected
    
    def date_filter(self) -> Dict[str, Any]:
        """Date range and period filters"""
        # Date range picker
        default_start_date = date(self.current_year, 1, 1)
        default_end_date = date.today()

        date_range = st.date_input(
            "📅 Datumsbereich",
            value=(default_start_date, default_end_date),
            help="Wählen Sie einen Start- und Enddatum für die Auswertung"
        )

        col1, col2, col3 = st.columns(3)

        # Handle reset flags
        month_index = 0
        quarter_index = 0

        if 'reset_month_filter' in st.session_state and st.session_state.reset_month_filter:
            month_index = 0
            del st.session_state.reset_month_filter

        if 'reset_quarter_filter' in st.session_state and st.session_state.reset_quarter_filter:
            quarter_index = 0
            del st.session_state.reset_quarter_filter

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
                index=month_index,
                help="Wählen Sie einen spezifischen Monat oder 'Alle'"
            )

        with col3:
            quarter = st.selectbox(
                "📅 Quartal",
                options=["Alle", "Q1", "Q2", "Q3", "Q4"],
                index=quarter_index,
                help="Wählen Sie ein Quartal"
            )

        # Convert filters to database format
        filters = {"year": year}

        # Add date range filter as tuple for database queries
        if isinstance(date_range, tuple) and len(date_range) == 2:
            filters["date_range"] = (date_range[0], date_range[1])
            filters["start_date"] = date_range[0]
            filters["end_date"] = date_range[1]
        elif isinstance(date_range, date):
            # Single date selected
            filters["date_range"] = (date_range, date_range)
            filters["start_date"] = date_range
            filters["end_date"] = date_range

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

        # Initialize or use existing selection
        if 'selected_activities' not in st.session_state:
            st.session_state.selected_activities = ["Alle"]

        selected_activities = st.multiselect(
            "🎯 Tätigkeiten Filter",
            options=["Alle"] + activities,
            default=st.session_state.selected_activities,
            help="Filtern Sie nach spezifischen Tätigkeiten"
        )

        st.session_state.selected_activities = selected_activities

        if "Alle" in selected_activities:
            return activities
        else:
            return selected_activities

    def customer_filter(self, df: pd.DataFrame) -> List[str]:
        """Filter by customer name (Kundenname)"""
        if df.empty:
            return []

        customers = sorted(df['Kundenname'].unique()) if 'Kundenname' in df.columns else []

        if not customers:
            return []

        selected_customers = st.multiselect(
            "👤 Kunden Filter",
            options=["Alle"] + customers,
            default=["Alle"],
            help="Filtern Sie nach spezifischen Kunden"
        )

        if "Alle" in selected_customers:
            return customers
        else:
            return selected_customers

    def employee_filter(self, df: pd.DataFrame) -> List[str]:
        """Filter by employee (Mitarbeiter)"""
        if df.empty:
            return []

        employees = sorted(df['Name'].unique()) if 'Name' in df.columns else []

        if not employees:
            return []

        selected_employees = st.multiselect(
            "👤 Mitarbeiter Filter",
            options=["Alle"] + employees,
            default=["Alle"],
            help="Filtern Sie nach spezifischen Mitarbeitern"
        )

        if "Alle" in selected_employees:
            return employees
        else:
            return selected_employees

    def search_filter(self) -> str:
        """Text search filter"""
        # Initialize or clear search term from session state
        if 'search_term' not in st.session_state:
            st.session_state.search_term = ''

        search_term = st.text_input(
            "🔍 Suche",
            value=st.session_state.search_term,
            placeholder="Suchen Sie in Projektnamen, Tätigkeiten oder Kommentaren...",
            help="Textsuche in verschiedenen Feldern"
        )

        st.session_state.search_term = search_term
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

        # Apply customer filter
        if 'selected_customers' in filters and filters['selected_customers']:
            if 'Kundenname' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['Kundenname'].isin(filters['selected_customers'])]

        # Apply employee filter
        if 'selected_employees' in filters and filters['selected_employees']:
            if 'Name' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['Name'].isin(filters['selected_employees'])]

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
    
    def show_filter_summary(self, filters: Dict[str, Any], record_count: int = None):
        """Show applied filters summary with record count"""
        # Build list of active filters with their metadata for individual clearing
        active_filters = []
        filter_details = []  # List of tuples: (display_text, filter_type, filter_key)

        if 'year' in filters:
            year_text = f"Jahr: {filters['year']}"
            active_filters.append(year_text)

        # Display date range if selected
        if 'start_date' in filters and 'end_date' in filters:
            start = filters['start_date']
            end = filters['end_date']
            start_str = start.strftime('%Y-%m-%d') if hasattr(start, 'strftime') else str(start)
            end_str = end.strftime('%Y-%m-%d') if hasattr(end, 'strftime') else str(end)
            date_text = f"Zeitraum: {start_str} bis {end_str}"
            active_filters.append(date_text)

        if 'month' in filters:
            month_text = f"Monat: {filters['month']:02d}"
            active_filters.append(month_text)
            filter_details.append((month_text, 'month', None))

        if 'quarter_months' in filters:
            quarters = {
                str([1,2,3]): "Q1",
                str([4,5,6]): "Q2",
                str([7,8,9]): "Q3",
                str([10,11,12]): "Q4"
            }
            quarter_key = str(filters['quarter_months'])
            if quarter_key in quarters:
                quarter_text = f"Quartal: {quarters[quarter_key]}"
                active_filters.append(quarter_text)
                filter_details.append((quarter_text, 'quarter', None))

        if 'selected_activities' in filters and filters['selected_activities']:
            if len(filters['selected_activities']) <= 3:
                activity_text = f"Tätigkeiten: {', '.join(filters['selected_activities'])}"
            else:
                activity_text = f"Tätigkeiten: {len(filters['selected_activities'])} ausgewählt"
            active_filters.append(activity_text)
            filter_details.append((activity_text, 'activities', None))

        if 'selected_customers' in filters and filters['selected_customers']:
            if len(filters['selected_customers']) <= 3:
                customer_text = f"Kunden: {', '.join(filters['selected_customers'])}"
            else:
                customer_text = f"Kunden: {len(filters['selected_customers'])} ausgewählt"
            active_filters.append(customer_text)
            filter_details.append((customer_text, 'customers', None))

        if 'selected_employees' in filters and filters['selected_employees']:
            if len(filters['selected_employees']) <= 3:
                employee_text = f"Mitarbeiter: {', '.join(filters['selected_employees'])}"
            else:
                employee_text = f"Mitarbeiter: {len(filters['selected_employees'])} ausgewählt"
            active_filters.append(employee_text)
            filter_details.append((employee_text, 'employees', None))

        if 'search_term' in filters and filters['search_term']:
            search_text = f"Suche: '{filters['search_term']}'"
            active_filters.append(search_text)
            filter_details.append((search_text, 'search', None))

        if active_filters:
            # Display prominent filter count badge and record count
            if record_count is not None:
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.metric("🔍 Aktive Filter", len(active_filters))

                with col2:
                    st.metric("📊 Datensätze", record_count)
            else:
                st.metric("🔍 Aktive Filter", len(active_filters))

            # Display each filter with individual clear button
            st.markdown("**Aktive Filter:**")
            for idx, (display_text, filter_type, _) in enumerate(filter_details):
                col1, col2 = st.columns([5, 1])

                with col1:
                    st.markdown(f"• {display_text}")

                with col2:
                    if st.button("❌", key=f"clear_filter_{filter_type}_{idx}", help=f"{display_text} entfernen"):
                        self._clear_individual_filter(filter_type)
                        st.rerun()

    def _clear_individual_filter(self, filter_type: str):
        """Clear a specific filter from session state"""
        if filter_type == 'month':
            # Set flag to reset month filter to "Alle"
            st.session_state['reset_month_filter'] = True
        elif filter_type == 'quarter':
            # Set flag to reset quarter filter to "Alle"
            st.session_state['reset_quarter_filter'] = True
        elif filter_type == 'activities':
            # Reset activities to "Alle"
            st.session_state['selected_activities'] = ["Alle"]
        elif filter_type == 'search':
            # Clear search term
            st.session_state['search_term'] = ''
        
    def reset_filters(self):
        """Reset all filters to default"""
        filter_keys = [
            'selected_projects',
            'selected_activities',
            'selected_customers',
            'search_term'
        ]

        for key in filter_keys:
            if key in st.session_state:
                del st.session_state[key]

        # Reset project checkboxes
        for key in list(st.session_state.keys()):
            if key.startswith("proj_"):
                del st.session_state[key]

        st.rerun()

# Global filter manager instance
filter_manager = FilterManager()
