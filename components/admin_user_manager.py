"""
Admin User Management Component
Allows admins to manage user-project assignments
"""
import streamlit as st
import json
import os
from typing import Dict, List, Any
from config.database import db_config

class AdminUserManager:
    """Manages user-project assignments for admins"""
    
    def __init__(self):
        self.users_file = "config/users.json"
    
    def load_users(self) -> Dict[str, Any]:
        """Load users from JSON file"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"users": {}, "default_permissions": ["read"]}
        except Exception as e:
            st.error(f"Fehler beim Laden der Benutzerdaten: {str(e)}")
            return {"users": {}, "default_permissions": ["read"]}
    
    def save_users(self, users_data: Dict[str, Any]) -> bool:
        """Save users to JSON file"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Fehler beim Speichern der Benutzerdaten: {str(e)}")
            return False
    
    def validate_projects(self, project_list: List[str]) -> Dict[str, bool]:
        """
        Validate if projects exist in ZV table
        
        Args:
            project_list: List of project IDs to validate
            
        Returns:
            Dict with project_id -> exists mapping
        """
        validation_results = {}
        
        for project_id in project_list:
            project_id_clean = project_id.strip()
            if project_id_clean:
                exists = db_config.validate_project_exists(project_id_clean)
                validation_results[project_id_clean] = exists
        
        return validation_results
    
    def parse_project_input(self, input_str: str) -> List[str]:
        """Parse comma-separated project input"""
        if not input_str:
            return []
        
        projects = [p.strip() for p in input_str.split(',')]
        return [p for p in projects if p]
    
    def show_user_management(self):
        """Display user management interface"""
        st.header("⚙️ Benutzerverwaltung")
        st.markdown("Verwaltung von Benutzer-Projekt-Zuordnungen")
        
        users_data = self.load_users()
        users = users_data.get('users', {})
        
        tab1, tab2 = st.tabs(["📝 Benutzer bearbeiten", "➕ Neuer Benutzer"])
        
        with tab1:
            if not users:
                st.info("Keine Benutzer vorhanden. Erstellen Sie einen neuen Benutzer im Tab 'Neuer Benutzer'.")
            else:
                selected_user = st.selectbox(
                    "Benutzer auswählen:",
                    options=list(users.keys()),
                    key="edit_user_select"
                )
                
                if selected_user:
                    self._show_user_editor(selected_user, users_data)
        
        with tab2:
            self._show_new_user_form(users_data)
    
    def _show_user_editor(self, user_email: str, users_data: Dict[str, Any]):
        """Show editor for existing user"""
        user_info = users_data['users'][user_email]
        current_projects = user_info.get('projects', [])
        current_permissions = user_info.get('permissions', [])
        
        st.subheader(f"Benutzer: {user_email}")
        
        st.markdown("#### Projektzuordnung")
        st.markdown("Geben Sie Projektkürzel kommasepariert ein (z.B. `P24SAN04, P24FBW06, P24SAN15`)")
        
        projects_input = st.text_area(
            "Projektkürzel:",
            value=", ".join(current_projects),
            height=100,
            key=f"projects_{user_email}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Validieren", key=f"validate_{user_email}"):
                project_list = self.parse_project_input(projects_input)
                
                if not project_list:
                    st.warning("Keine Projekte eingegeben")
                else:
                    validation_results = self.validate_projects(project_list)
                    
                    valid_projects = [p for p, exists in validation_results.items() if exists]
                    invalid_projects = [p for p, exists in validation_results.items() if not exists]
                    
                    if valid_projects:
                        st.success(f"✅ Gültige Projekte ({len(valid_projects)}):")
                        st.code(", ".join(valid_projects))
                    
                    if invalid_projects:
                        st.error(f"❌ Nicht gefundene Projekte ({len(invalid_projects)}):")
                        st.code(", ".join(invalid_projects))
                        st.warning("Diese Projekte existieren nicht in der ZV-Tabelle!")
        
        with col2:
            if st.button("💾 Speichern", key=f"save_{user_email}", type="primary"):
                project_list = self.parse_project_input(projects_input)
                
                users_data['users'][user_email]['projects'] = project_list
                
                if self.save_users(users_data):
                    st.success(f"✅ Projekte für {user_email} gespeichert!")
                    st.rerun()
        
        st.markdown("#### Berechtigungen")
        
        available_permissions = ["read", "export", "edit_targets", "admin"]
        
        selected_permissions = st.multiselect(
            "Berechtigungen:",
            options=available_permissions,
            default=current_permissions,
            key=f"perms_{user_email}"
        )
        
        if st.button("💾 Berechtigungen speichern", key=f"save_perms_{user_email}"):
            users_data['users'][user_email]['permissions'] = selected_permissions
            
            if self.save_users(users_data):
                st.success(f"✅ Berechtigungen für {user_email} aktualisiert!")
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🗑️ Benutzer löschen", key=f"delete_{user_email}"):
            if st.session_state.get(f'confirm_delete_{user_email}', False):
                del users_data['users'][user_email]
                if self.save_users(users_data):
                    st.success(f"Benutzer {user_email} gelöscht")
                    st.rerun()
            else:
                st.session_state[f'confirm_delete_{user_email}'] = True
                st.warning("⚠️ Klicken Sie erneut zum Bestätigen")
    
    def _show_new_user_form(self, users_data: Dict[str, Any]):
        """Show form to create new user"""
        st.subheader("Neuen Benutzer anlegen")
        
        new_email = st.text_input(
            "E-Mail-Adresse:",
            placeholder="name@example.com",
            key="new_user_email"
        )
        
        st.markdown("#### Projektzuordnung")
        st.markdown("Geben Sie Projektkürzel kommasepariert ein (z.B. `P24SAN04, P24FBW06, P24SAN15`)")
        
        new_projects_input = st.text_area(
            "Projektkürzel:",
            height=100,
            key="new_user_projects"
        )
        
        if st.button("🔍 Projekte validieren", key="validate_new"):
            project_list = self.parse_project_input(new_projects_input)
            
            if not project_list:
                st.warning("Keine Projekte eingegeben")
            else:
                validation_results = self.validate_projects(project_list)
                
                valid_projects = [p for p, exists in validation_results.items() if exists]
                invalid_projects = [p for p, exists in validation_results.items() if not exists]
                
                if valid_projects:
                    st.success(f"✅ Gültige Projekte ({len(valid_projects)}):")
                    st.code(", ".join(valid_projects))
                
                if invalid_projects:
                    st.error(f"❌ Nicht gefundene Projekte ({len(invalid_projects)}):")
                    st.code(", ".join(invalid_projects))
                    st.warning("Diese Projekte existieren nicht in der ZV-Tabelle!")
        
        st.markdown("#### Berechtigungen")
        
        available_permissions = ["read", "export", "edit_targets", "admin"]
        
        new_permissions = st.multiselect(
            "Berechtigungen:",
            options=available_permissions,
            default=["read"],
            key="new_user_permissions"
        )
        
        st.markdown("---")
        
        if st.button("➕ Benutzer erstellen", type="primary", key="create_user"):
            if not new_email or '@' not in new_email:
                st.error("❌ Bitte geben Sie eine gültige E-Mail-Adresse ein")
            elif new_email in users_data.get('users', {}):
                st.error(f"❌ Benutzer {new_email} existiert bereits")
            else:
                project_list = self.parse_project_input(new_projects_input)
                
                users_data['users'][new_email] = {
                    'projects': project_list,
                    'permissions': new_permissions
                }
                
                if self.save_users(users_data):
                    st.success(f"✅ Benutzer {new_email} erfolgreich erstellt!")
                    st.rerun()

admin_user_manager = AdminUserManager()
