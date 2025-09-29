"""
Authentication component with Entra ID integration and fallback
"""
import os
import json
import streamlit as st
from typing import Optional, Dict, Any
import requests
import logging

# Import msal only if not in test mode or if available
try:
    import msal
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False
    logging.warning("msal not available - authentication will use fallback mode only")

class AuthManager:
    """Authentication manager with Entra ID and local fallback"""
    
    def __init__(self):
        # Check for test mode
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        
        self.client_id = os.getenv('ENTRA_CLIENT_ID', '')
        self.client_secret = os.getenv('ENTRA_CLIENT_SECRET', '')
        self.tenant_id = os.getenv('ENTRA_TENANT_ID', '')
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        self.redirect_uri = "http://localhost:8501"
        
        # Load user configuration
        self.users_config = self._load_users_config()
        
        # Initialize MSAL app if Entra ID is configured and not in test mode
        if not self.test_mode and self.client_id and self.client_secret and self.tenant_id and MSAL_AVAILABLE:
            self.app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )
        else:
            self.app = None
            
    def _load_users_config(self) -> Dict[str, Any]:
        """Load user configuration from JSON file"""
        config_file = 'config/users.json'
        
        # Use test users in test mode
        if self.test_mode:
            test_config_file = 'test_data/test_users.json'
            if os.path.exists(test_config_file):
                config_file = test_config_file
        
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load users config from {config_file}: {e}")
            # Return test-friendly default config
            if self.test_mode:
                return {
                    "users": {
                        "test@intend.com": {
                            "projects": ["P24SAN06", "P24XYZ01", "P24ABC02"],
                            "permissions": ["read", "export", "edit_targets", "admin"]
                        }
                    },
                    "default_permissions": ["read"]
                }
            return {"users": {}, "default_permissions": ["read"]}
    
    def is_entra_configured(self) -> bool:
        """Check if Entra ID is properly configured"""
        return bool(self.client_id and self.client_secret and self.tenant_id and self.app and MSAL_AVAILABLE)
    
    def get_auth_url(self) -> str:
        """Get Entra ID authentication URL"""
        if not self.app:
            return ""
            
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scope,
            redirect_uri=self.redirect_uri
        )
        return auth_url
    
    def authenticate_with_code(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with authorization code"""
        if not self.app:
            return None
            
        try:
            result = self.app.acquire_token_by_authorization_code(
                auth_code,
                scopes=self.scope,
                redirect_uri=self.redirect_uri
            )
            
            if "access_token" in result:
                # Get user info from Microsoft Graph
                user_info = self._get_user_info(result["access_token"])
                return user_info
            else:
                logging.error(f"Authentication failed: {result.get('error_description')}")
                return None
                
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return None
    
    def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Microsoft Graph"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        try:
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                    'name': user_data.get('displayName', ''),
                    'id': user_data.get('id', ''),
                    'access_token': access_token
                }
            else:
                logging.error(f"Failed to get user info: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error getting user info: {e}")
            return None
    
    def get_user_permissions(self, email: str) -> Dict[str, Any]:
        """Get user permissions and accessible projects"""
        user_config = self.users_config.get("users", {}).get(email)
        
        if user_config:
            return {
                'projects': user_config.get('projects', []),
                'permissions': user_config.get('permissions', self.users_config.get('default_permissions', ['read']))
            }
        else:
            # Return default permissions for unknown users
            return {
                'projects': [],
                'permissions': self.users_config.get('default_permissions', ['read'])
            }
    
    def has_permission(self, email: str, permission: str) -> bool:
        """Check if user has specific permission"""
        user_perms = self.get_user_permissions(email)
        return permission in user_perms.get('permissions', [])
    
    def login_form(self) -> Optional[Dict[str, Any]]:
        """Display login form and handle authentication"""
        
        # Check if user is already logged in
        if 'user' in st.session_state and st.session_state.user:
            return st.session_state.user
        
        # TEST MODE - Auto login without authentication
        if self.test_mode:
            return self.test_mode_login()
        
        # Handle authentication code from URL
        query_params = st.query_params
        if 'code' in query_params:
            auth_code = query_params['code']
            user = self.authenticate_with_code(auth_code)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Authentifizierung fehlgeschlagen")
        
        st.title("🔐 SQL Server Dashboard - Anmeldung")
        
        if self.is_entra_configured():
            # Entra ID login
            st.markdown("### Microsoft Entra ID Anmeldung")
            
            if st.button("Mit Microsoft anmelden", type="primary"):
                auth_url = self.get_auth_url()
                if auth_url:
                    st.markdown(f"[Hier klicken für Anmeldung]({auth_url})")
                    st.info("Sie werden zu Microsoft weitergeleitet. Nach der Anmeldung kehren Sie automatisch zurück.")
                else:
                    st.error("Fehler bei der Authentifizierungsurl-Generierung")
            
            st.markdown("---")
        
        # Development/Local login fallback
        st.markdown("### Entwicklungsumgebung - Lokale Anmeldung")
        st.info("Für lokale Entwicklung ohne Entra ID")
        
        with st.form("local_login"):
            email = st.text_input("E-Mail-Adresse", value="admin@intend.com")
            name = st.text_input("Name", value="Test User")
            submit = st.form_submit_button("Anmelden", type="primary")
            
            if submit and email:
                # Validate user exists in config
                if email in self.users_config.get("users", {}):
                    user = {
                        'email': email,
                        'name': name,
                        'id': email,
                        'access_token': 'local_dev_token'
                    }
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Benutzer nicht in der Konfiguration gefunden")
        
        # Show available test users
        with st.expander("Verfügbare Test-Benutzer"):
            for email, config in self.users_config.get("users", {}).items():
                st.write(f"**{email}**")
                st.write(f"- Projekte: {', '.join(config.get('projects', []))}")
                st.write(f"- Berechtigungen: {', '.join(config.get('permissions', []))}")
                st.write("---")
        
        return None
    
    def test_mode_login(self) -> Dict[str, Any]:
        """Handle test mode login without authentication"""
        st.title("🧪 TEST-Modus - SQL Server Dashboard")
        
        st.success("🚀 **TEST-UMGEBUNG AKTIV**")
        st.info("✨ Keine Authentifizierung erforderlich - Verwende Dummy-Daten")
        
        # Show available test users
        available_users = list(self.users_config.get("users", {}).keys())
        
        if not available_users:
            available_users = ["test@intend.com"]
        
        # Auto-select first user or allow selection
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_user = st.selectbox(
                "🧪 Test-Benutzer auswählen:",
                options=available_users,
                index=0,
                help="Wählen Sie einen Test-Benutzer für die Demo"
            )
        
        with col2:
            auto_login = st.checkbox("Auto-Login", value=True, help="Automatisch anmelden")
        
        # Auto login or manual login
        if auto_login or st.button("🧪 Test-Login", type="primary"):
            user = {
                'email': selected_user,
                'name': f"Test User ({selected_user.split('@')[0]})",
                'id': selected_user,
                'access_token': 'test_mode_token',
                'test_mode': True
            }
            st.session_state.user = user
            st.rerun()
        
        # Show test environment info
        with st.expander("ℹ️ Test-Umgebung Information", expanded=False):
            st.markdown("""
            **TEST-MODUS ist aktiv:**
            - 🔓 **Keine Entra ID Authentifizierung**
            - 📊 **Dummy-Daten werden verwendet**
            - 🧪 **Alle Features verfügbar**
            - ⚡ **Schneller Setup für Demo/Entwicklung**
            
            **Verfügbare Test-Benutzer:**
            """)
            
            for email, config in self.users_config.get("users", {}).items():
                st.write(f"**{email}**")
                st.write(f"- Projekte: {', '.join(config.get('projects', []))}")
                st.write(f"- Berechtigungen: {', '.join(config.get('permissions', []))}")
                st.write("---")
        
        return None
    
    def logout(self):
        """Logout current user"""
        if 'user' in st.session_state:
            del st.session_state.user
        
        # Clear all session state related to user
        keys_to_remove = []
        for key in st.session_state.keys():
            if key.startswith('user') or key in ['selected_projects', 'dashboard_editor']:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        # Force a complete rerun
        st.rerun()
    
    def show_user_info(self):
        """Show current user information in sidebar"""
        if 'user' not in st.session_state or not st.session_state.user:
            return
            
        user = st.session_state.user
        user_perms = self.get_user_permissions(user['email'])
        
        with st.sidebar:
            st.markdown("### 👤 Benutzer")
            st.write(f"**{user['name']}**")
            st.write(f"*{user['email']}*")
            
            st.markdown("**Berechtigungen:**")
            for perm in user_perms['permissions']:
                st.write(f"✓ {perm}")
            
            st.markdown("**Projekte:**")
            for project in user_perms['projects']:
                st.write(f"📁 {project}")
            
            if st.button("Abmelden", type="secondary"):
                self.logout()

# Global auth manager instance
auth_manager = AuthManager()
