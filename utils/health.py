"""
Health check utilities for monitoring application status
"""
import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, Any
import requests
from components.auth import auth_manager

# Import database config based on environment
if os.getenv('TEST_MODE', 'false').lower() == 'true':
    from config.test_database import test_db_config as db_config
else:
    from config.database import db_config

class HealthChecker:
    """Application health monitoring"""
    
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'authentication': self.check_authentication,
            'filesystem': self.check_filesystem,
            'configuration': self.check_configuration
        }
    
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            is_connected = db_config.test_connection()
            return {
                'status': 'healthy' if is_connected else 'unhealthy',
                'message': 'Database connection successful' if is_connected else 'Database connection failed',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Database check error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def check_authentication(self) -> Dict[str, Any]:
        """Check authentication service"""
        try:
            if auth_manager.is_entra_configured():
                # Try to access Microsoft Graph discovery endpoint
                try:
                    response = requests.get(
                        'https://login.microsoftonline.com/common/v2.0/.well-known/openid_configuration',
                        timeout=5
                    )
                    if response.status_code == 200:
                        return {
                            'status': 'healthy',
                            'message': 'Entra ID authentication configured and reachable',
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'status': 'degraded',
                            'message': f'Entra ID endpoint returned {response.status_code}',
                            'timestamp': datetime.now().isoformat()
                        }
                except requests.RequestException as e:
                    return {
                        'status': 'degraded',
                        'message': f'Entra ID not reachable: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                return {
                    'status': 'healthy',
                    'message': 'Local authentication mode (development)',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Authentication check error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem access for cache and config"""
        try:
            required_dirs = ['config', 'cache']
            issues = []
            
            for dir_name in required_dirs:
                if not os.path.exists(dir_name):
                    try:
                        os.makedirs(dir_name)
                    except Exception as e:
                        issues.append(f"Cannot create {dir_name}: {str(e)}")
                elif not os.access(dir_name, os.W_OK):
                    issues.append(f"No write access to {dir_name}")
            
            # Test file write
            try:
                test_file = 'cache/health_check.tmp'
                with open(test_file, 'w') as f:
                    f.write('health_check')
                os.remove(test_file)
            except Exception as e:
                issues.append(f"Cannot write test file: {str(e)}")
            
            if issues:
                return {
                    'status': 'degraded',
                    'message': f'Filesystem issues: {"; ".join(issues)}',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'healthy',
                    'message': 'Filesystem access normal',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Filesystem check error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def check_configuration(self) -> Dict[str, Any]:
        """Check configuration files"""
        try:
            issues = []
            
            # Check users.json
            if os.path.exists('config/users.json'):
                try:
                    with open('config/users.json', 'r') as f:
                        users_config = json.load(f)
                        if not users_config.get('users'):
                            issues.append('No users configured')
                except json.JSONDecodeError:
                    issues.append('Invalid users.json format')
                except Exception as e:
                    issues.append(f'Cannot read users.json: {str(e)}')
            else:
                issues.append('users.json not found')
            
            # Check environment variables
            required_env_vars = ['SQL_SERVER_HOST', 'SQL_SERVER_DATABASE']
            missing_env_vars = [var for var in required_env_vars if not os.getenv(var)]
            
            if missing_env_vars:
                issues.append(f'Missing environment variables: {", ".join(missing_env_vars)}')
            
            if issues:
                return {
                    'status': 'degraded',
                    'message': f'Configuration issues: {"; ".join(issues)}',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'healthy',
                    'message': 'Configuration valid',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Configuration check error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_status = 'healthy'
        
        for check_name, check_func in self.checks.items():
            results[check_name] = check_func()
            
            # Determine overall status
            if results[check_name]['status'] == 'unhealthy':
                overall_status = 'unhealthy'
            elif results[check_name]['status'] == 'degraded' and overall_status == 'healthy':
                overall_status = 'degraded'
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': results
        }
    
    def get_health_json(self) -> str:
        """Get health status as JSON string"""
        health_data = self.run_all_checks()
        return json.dumps(health_data, indent=2)
    
    def show_health_dashboard(self):
        """Show health dashboard in Streamlit"""
        st.subheader("🏥 System Health Check")
        
        health_data = self.run_all_checks()
        overall_status = health_data['overall_status']
        
        # Overall status
        status_colors = {
            'healthy': '🟢',
            'degraded': '🟡', 
            'unhealthy': '🔴'
        }
        
        st.markdown(f"**Overall Status:** {status_colors.get(overall_status, '⚫')} {overall_status.upper()}")
        st.markdown(f"**Last Check:** {health_data['timestamp']}")
        
        # Individual checks
        for check_name, check_result in health_data['checks'].items():
            with st.expander(f"{status_colors.get(check_result['status'], '⚫')} {check_name.title()}"):
                st.write(f"**Status:** {check_result['status']}")
                st.write(f"**Message:** {check_result['message']}")
                st.write(f"**Timestamp:** {check_result['timestamp']}")
        
        # Refresh button
        if st.button("🔄 Refresh Health Check"):
            st.cache_data.clear()
            st.rerun()

# Global health checker instance
health_checker = HealthChecker()
