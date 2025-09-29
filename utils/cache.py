"""
Caching utilities for performance optimization
"""
import streamlit as st
import pandas as pd
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib

class CacheManager:
    """Cache manager for database queries and user data"""
    
    def __init__(self):
        self.cache_dir = "cache"
        self.ensure_cache_dir()
        
    def ensure_cache_dir(self):
        """Ensure cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_cache_key(self, prefix: str, **params) -> str:
        """Generate cache key from parameters"""
        params_str = json.dumps(params, sort_keys=True)
        hash_obj = hashlib.md5(params_str.encode())
        return f"{prefix}_{hash_obj.hexdigest()}"
    
    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def cache_user_projects(_self, user_email: str, projects: list) -> list:
        """Cache user's accessible projects"""
        return projects
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def cache_project_data(_self, projects: list, filters: Dict[str, Any]) -> pd.DataFrame:
        """Cache project time data with filters applied"""
        # This would be implemented with actual database call
        # For now, return empty DataFrame as placeholder
        return pd.DataFrame()
    
    @st.cache_data(ttl=1800)  # Cache for 30 minutes
    def cache_target_hours(_self, project: str, activity: str) -> Optional[float]:
        """Cache target hours for specific activity"""
        cache_key = f"targets_{project}_{activity}"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    # Check if cache is still valid (24 hours)
                    cache_time = datetime.fromisoformat(data.get('timestamp', ''))
                    if datetime.now() - cache_time < timedelta(hours=24):
                        return data.get('target_hours')
            except Exception:
                pass
        
        return None
    
    def save_target_hours(self, project: str, activity: str, target_hours: float):
        """Save target hours to cache/filesystem"""
        cache_key = f"targets_{project}_{activity}"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        data = {
            'project': project,
            'activity': activity,
            'target_hours': target_hours,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            st.error(f"Failed to save target hours: {e}")
    
    def load_all_target_hours(self) -> Dict[str, Dict[str, float]]:
        """Load all cached target hours"""
        targets = {}
        
        if not os.path.exists(self.cache_dir):
            return targets
        
        for filename in os.listdir(self.cache_dir):
            if filename.startswith('targets_') and filename.endswith('.json'):
                filepath = os.path.join(self.cache_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        project = data.get('project')
                        activity = data.get('activity')
                        target_hours = data.get('target_hours')
                        
                        if project and activity and target_hours is not None:
                            if project not in targets:
                                targets[project] = {}
                            targets[project][activity] = target_hours
                            
                except Exception:
                    continue
        
        return targets
    
    def clear_cache(self, cache_type: str = "all"):
        """Clear specific or all cache"""
        if cache_type == "all":
            # Clear Streamlit cache
            st.cache_data.clear()
            
            # Clear file cache
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
        
        elif cache_type == "targets":
            # Clear only target hours cache
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    if filename.startswith('targets_'):
                        filepath = os.path.join(self.cache_dir, filename)
                        try:
                            os.remove(filepath)
                        except Exception:
                            pass
        
        elif cache_type == "data":
            # Clear only data cache (Streamlit cache)
            st.cache_data.clear()

# Global cache manager instance
cache_manager = CacheManager()
