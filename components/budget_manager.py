"""
Budget Management Component
Manages project budget entries with time-based validity
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Dict, Optional, List
import logging

# Import database config based on environment
import os
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

if TEST_MODE:
    from config.test_database import test_db_config as budget_db
else:
    from config.budget_database import budget_db


class BudgetManager:
    """Manages budget entries with time-based validity tracking"""

    def __init__(self):
        self.change_types = {
            'initial': '🆕 Initial Budget (Erstbudget)',
            'extension': '📈 Extension (Budgeterweiterung)',
            'correction': '🔧 Correction (Korrektur)',
            'reduction': '📉 Reduction (Budgetreduzierung)'
        }

    def show_budget_management(self, user_email: str, user_projects: List[str]):
        """
        Main budget management interface

        Args:
            user_email: Current user's email
            user_projects: List of projects accessible to the user
        """
        st.header("💰 Budget-Verwaltung")

        st.markdown("""
        Hier können Sie Projektbudgets (Sollstunden) erfassen und anpassen.
        Alle Änderungen werden mit vollständiger Historie und Zeitstempel gespeichert.
        """)

        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs([
            "📊 Budget-Übersicht",
            "➕ Budget erfassen/anpassen",
            "📜 Änderungshistorie"
        ])

        with tab1:
            self._show_budget_overview(user_projects)

        with tab2:
            self._show_budget_entry_form(user_email, user_projects)

        with tab3:
            self._show_budget_history(user_projects)

    def _show_budget_overview(self, user_projects: List[str]):
        """Show current budget overview for all projects"""
        st.subheader("📊 Aktuelle Projekt-Budgets")

        # Date selector for budget calculation
        target_date = st.date_input(
            "Stichtag für Budget-Berechnung",
            value=date.today(),
            help="Zeigt die Budgets an, die zum ausgewählten Datum gültig waren/sind"
        )

        # Load budgets for all projects at target date
        budgets = budget_db.get_all_budgets_at_date(
            user_projects,
            target_date.isoformat()
        )

        if not budgets:
            st.info("Noch keine Budgets erfasst. Verwenden Sie den Tab 'Budget erfassen/anpassen' zum Hinzufügen.")
            return

        # Prepare data for display
        budget_data = []
        for project_id, activities in budgets.items():
            project_total = sum(activities.values())
            for activity, hours in activities.items():
                percentage = (hours / project_total * 100) if project_total > 0 else 0
                budget_data.append({
                    'Projekt': project_id,
                    'Tätigkeit': activity,
                    'Sollstunden': hours,
                    'Anteil am Projekt (%)': round(percentage, 1)
                })

        budget_df = pd.DataFrame(budget_data)

        # Show summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_projects = len(budgets)
            st.metric("Projekte mit Budget", total_projects)

        with col2:
            total_activities = len(budget_df)
            st.metric("Tätigkeiten", total_activities)

        with col3:
            total_hours = budget_df['Sollstunden'].sum()
            st.metric("Gesamtbudget (Stunden)", f"{total_hours:.1f}h")

        with col4:
            avg_hours = budget_df['Sollstunden'].mean()
            st.metric("Ø Stunden/Tätigkeit", f"{avg_hours:.1f}h")

        # Display by project
        st.markdown("### Details nach Projekt")

        for project_id in sorted(budgets.keys()):
            project_df = budget_df[budget_df['Projekt'] == project_id].copy()
            project_total = project_df['Sollstunden'].sum()

            with st.expander(f"📂 {project_id} - Gesamt: {project_total:.1f}h", expanded=True):
                # Configure columns
                column_config = {
                    'Sollstunden': st.column_config.NumberColumn(
                        'Sollstunden',
                        format="%.1f h"
                    ),
                    'Anteil am Projekt (%)': st.column_config.NumberColumn(
                        'Anteil am Projekt (%)',
                        format="%.1f%%"
                    )
                }

                st.dataframe(
                    project_df[['Tätigkeit', 'Sollstunden', 'Anteil am Projekt (%)']],
                    column_config=column_config,
                    hide_index=True,
                    use_container_width=True
                )

    def _show_budget_entry_form(self, user_email: str, user_projects: List[str]):
        """Show form for adding new budget entries"""
        st.subheader("➕ Budget erfassen oder anpassen")

        st.markdown("""
        Erfassen Sie hier neue Budgets oder passen Sie bestehende Budgets an.
        Jede Änderung wird mit vollständiger Dokumentation gespeichert.
        """)

        with st.form("budget_entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                # Project selection
                selected_project = st.selectbox(
                    "Projekt *",
                    options=user_projects,
                    help="Wählen Sie das Projekt aus"
                )

                # Load existing activities for this project from database
                # Try to get activities from the main db_config first
                existing_activities = []
                try:
                    # Import db_config to access project activities
                    import os
                    TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
                    if TEST_MODE:
                        from config.test_database import test_db_config as db_config
                    else:
                        from config.database import db_config

                    # Get activities from aggregated data
                    existing_activities = db_config.get_all_activities_for_project(selected_project)
                except Exception as e:
                    logging.warning(f"Could not load activities from db_config: {e}")
                    # Fallback: try to get from budget_db
                    try:
                        existing_activities = budget_db.get_all_activities_for_project(selected_project)
                    except Exception as e2:
                        logging.warning(f"Could not load activities from budget_db: {e2}")

                # Add option for new activity
                activity_options = ["➕ Neue Tätigkeit..."] + sorted(existing_activities)

                # Activity selection
                activity_choice = st.selectbox(
                    "Tätigkeit *",
                    options=activity_options,
                    help="Wählen Sie eine bestehende Tätigkeit oder erstellen Sie eine neue"
                )

                # If new activity, show text input
                if activity_choice == "➕ Neue Tätigkeit...":
                    activity = st.text_input(
                        "Name der neuen Tätigkeit *",
                        placeholder="z.B. Implementierung, Testing, Projektmanagement",
                        help="Geben Sie die Tätigkeitsbezeichnung ein"
                    )
                else:
                    activity = activity_choice

                # Hours input
                hours = st.number_input(
                    "Stunden *",
                    min_value=0.0,
                    max_value=10000.0,
                    value=0.0,
                    step=0.5,
                    help="Anzahl der Stunden für diese Budgetänderung"
                )

            with col2:
                # Change type
                change_type = st.selectbox(
                    "Änderungstyp *",
                    options=list(self.change_types.keys()),
                    format_func=lambda x: self.change_types[x],
                    help="Art der Budgetänderung"
                )

                # Valid from date
                valid_from = st.date_input(
                    "Gültig ab *",
                    value=date.today(),
                    help="Ab diesem Datum ist die Budgetänderung gültig"
                )

                # Reference
                reference = st.text_input(
                    "Referenz (optional)",
                    placeholder="z.B. Vertrag-2024-001, CR-042",
                    help="Vertragsnummer, Change Request, etc."
                )

            # Reason (full width)
            reason = st.text_area(
                "Begründung *",
                placeholder="Beschreiben Sie den Grund für diese Budgetänderung...",
                help="Pflichtfeld: Erläutern Sie die Budgetänderung",
                height=100
            )

            # Preview section
            if activity and hours > 0:
                st.markdown("---")
                st.markdown("### 👁️ Vorschau")

                # Calculate current budget
                current_budget = budget_db.get_budget_at_date(
                    selected_project,
                    activity,
                    date.today().isoformat()
                )

                col_prev1, col_prev2, col_prev3 = st.columns(3)

                with col_prev1:
                    st.metric("Aktuelles Budget", f"{current_budget:.1f}h")

                with col_prev2:
                    st.metric("Änderung", f"{hours:.1f}h")

                with col_prev3:
                    new_budget = current_budget + hours
                    st.metric("Neues Budget", f"{new_budget:.1f}h")

            # Submit button
            submitted = st.form_submit_button(
                "💾 Budget speichern",
                type="primary",
                use_container_width=True
            )

            if submitted:
                # Validate inputs
                if not activity or not activity.strip():
                    st.error("❌ Bitte geben Sie eine Tätigkeit an")
                    return

                if hours <= 0:
                    st.error("❌ Stunden müssen größer als 0 sein")
                    return

                if not reason or not reason.strip():
                    st.error("❌ Bitte geben Sie eine Begründung an")
                    return

                # Save to database
                success = budget_db.save_budget_entry(
                    project_id=selected_project,
                    activity=activity.strip(),
                    hours=hours,
                    change_type=change_type,
                    valid_from=valid_from.isoformat(),
                    reason=reason.strip(),
                    reference=reference.strip() if reference else None,
                    created_by=user_email
                )

                if success:
                    st.success(f"""
                    ✅ Budget erfolgreich gespeichert!

                    - Projekt: {selected_project}
                    - Tätigkeit: {activity}
                    - Stunden: {hours:.1f}h
                    - Gültig ab: {valid_from.strftime('%d.%m.%Y')}
                    """)

                    # Clear cache to reflect changes
                    st.cache_data.clear()
                else:
                    st.error("❌ Fehler beim Speichern des Budgets. Bitte versuchen Sie es erneut.")

    def _show_budget_history(self, user_projects: List[str]):
        """Show complete budget change history"""
        st.subheader("📜 Budget-Änderungshistorie")

        # Project selection
        selected_project = st.selectbox(
            "Projekt auswählen",
            options=["Alle Projekte"] + user_projects,
            key="history_project_selector"
        )

        # Load history
        if selected_project == "Alle Projekte":
            # Load history for all projects
            history_dfs = []
            for project_id in user_projects:
                project_history = budget_db.get_budget_history(project_id)
                if not project_history.empty:
                    history_dfs.append(project_history)

            if history_dfs:
                history_df = pd.concat(history_dfs, ignore_index=True)
            else:
                history_df = pd.DataFrame()
        else:
            history_df = budget_db.get_budget_history(selected_project)

        if history_df.empty:
            st.info("Keine Budget-Historie verfügbar für die ausgewählten Projekte")
            return

        # Add display columns
        history_df['ChangeTypeDisplay'] = history_df['ChangeType'].map(
            lambda x: self.change_types.get(x, x)
        )

        # Format dates
        history_df['ValidFromDisplay'] = pd.to_datetime(
            history_df['ValidFrom']
        ).dt.strftime('%d.%m.%Y')

        history_df['CreatedAtDisplay'] = pd.to_datetime(
            history_df['CreatedAt']
        ).dt.strftime('%d.%m.%Y %H:%M')

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            total_entries = len(history_df)
            st.metric("Gesamt-Änderungen", total_entries)

        with col2:
            total_hours = history_df['Hours'].sum()
            st.metric("Gesamtsumme Stunden", f"{total_hours:.1f}h")

        with col3:
            unique_activities = history_df['Activity'].nunique()
            st.metric("Tätigkeiten", unique_activities)

        # Filter options
        st.markdown("### 🔍 Filter")

        col_filter1, col_filter2 = st.columns(2)

        with col_filter1:
            # Activity filter
            all_activities = ["Alle"] + sorted(history_df['Activity'].unique().tolist())
            selected_activity = st.selectbox(
                "Tätigkeit",
                options=all_activities,
                key="history_activity_filter"
            )

        with col_filter2:
            # Change type filter
            all_change_types = ["Alle"] + list(self.change_types.keys())
            selected_change_type = st.selectbox(
                "Änderungstyp",
                options=all_change_types,
                format_func=lambda x: self.change_types.get(x, x) if x != "Alle" else "Alle",
                key="history_change_type_filter"
            )

        # Apply filters
        filtered_df = history_df.copy()

        if selected_activity != "Alle":
            filtered_df = filtered_df[filtered_df['Activity'] == selected_activity]

        if selected_change_type != "Alle":
            filtered_df = filtered_df[filtered_df['ChangeType'] == selected_change_type]

        # Display history
        st.markdown("### 📋 Änderungsliste")

        # Prepare display dataframe
        display_df = filtered_df[[
            'ProjectID',
            'Activity',
            'Hours',
            'ChangeTypeDisplay',
            'ValidFromDisplay',
            'Reason',
            'Reference',
            'CreatedBy',
            'CreatedAtDisplay'
        ]].copy()

        display_df.columns = [
            'Projekt',
            'Tätigkeit',
            'Stunden',
            'Typ',
            'Gültig ab',
            'Begründung',
            'Referenz',
            'Erstellt von',
            'Erstellt am'
        ]

        # Column configuration
        column_config = {
            'Stunden': st.column_config.NumberColumn(
                'Stunden',
                format="%.1f h"
            )
        }

        st.dataframe(
            display_df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True
        )

        # Export option
        st.markdown("---")
        st.markdown("### 📥 Export")

        if st.button("📥 Historie als CSV exportieren"):
            csv_data = display_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="💾 CSV herunterladen",
                data=csv_data,
                file_name=f"budget_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )


# Global instance
budget_manager = BudgetManager()
