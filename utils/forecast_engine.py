"""
Sprint-basiertes Forecasting mit Szenarien-Analyse
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import streamlit as st
import json
import os

# Konstanten
SPRINT_DURATION_DAYS = 14
ANALYSIS_SPRINTS = 4
SPRINT_WEIGHTS = [0.10, 0.20, 0.30, 0.40]  # Sprint 1-4 (alt zu neu)

class ForecastEngine:
    """
    Sprint-basierte Forecast-Berechnungen mit Szenarien.
    """
    
    def __init__(self, bookings_df: pd.DataFrame, target_hours: float):
        """
        Args:
            bookings_df: DataFrame mit [DatumBuchung, Stunden]
            target_hours: Sollstunden
        """
        self.bookings_df = bookings_df.copy()
        self.target_hours = target_hours
        self.today = datetime.now()
        
        # Berechne Sprint-Daten
        self.sprint_data = self._calculate_sprint_data()
        
    def _calculate_sprint_data(self) -> pd.DataFrame:
        """
        Aggregiert Buchungen nach 2-Wochen-Sprints.
        
        Returns:
            DataFrame mit [sprint_number, sprint_start, sprint_end, hours, weight]
        """
        if self.bookings_df.empty:
            return pd.DataFrame()
        
        # Berechne Sprint-Nummer für jede Buchung
        self.bookings_df['DatumBuchung'] = pd.to_datetime(self.bookings_df['DatumBuchung'])
        self.bookings_df['days_ago'] = (self.today - self.bookings_df['DatumBuchung']).dt.days
        self.bookings_df['sprint_number'] = (self.bookings_df['days_ago'] // SPRINT_DURATION_DAYS)
        
        # Filtere auf letzte 4 Sprints
        recent_bookings = self.bookings_df[self.bookings_df['sprint_number'] < ANALYSIS_SPRINTS].copy()
        
        if recent_bookings is None or len(recent_bookings) == 0:
            return pd.DataFrame()
        
        # Aggregiere nach Sprint
        sprint_data = recent_bookings.groupby('sprint_number').agg({
            'Stunden': 'sum',
            'DatumBuchung': ['min', 'max']
        }).reset_index()
        
        sprint_data.columns = ['sprint_number', 'hours', 'sprint_start', 'sprint_end']
        
        # Füge Gewichte hinzu (umgekehrt, da sprint_number 0 = neuester)
        sprint_data['weight'] = sprint_data['sprint_number'].apply(
            lambda x: SPRINT_WEIGHTS[ANALYSIS_SPRINTS - 1 - x] if x < ANALYSIS_SPRINTS else 0
        )
        
        return sprint_data.sort_values('sprint_number')
    
    def calculate_weighted_sprint_average(self) -> float:
        """
        Berechnet gewichteten Durchschnitt über 4 Sprints.
        
        Returns:
            Durchschnittliche Stunden pro Sprint
        """
        if self.sprint_data is None or len(self.sprint_data) == 0:
            return 0.0
        
        # Gewichteter Durchschnitt
        weighted_hours = (self.sprint_data['hours'] * self.sprint_data['weight']).sum()
        total_weight = self.sprint_data['weight'].sum()
        
        if total_weight == 0:
            return self.sprint_data['hours'].mean()
        
        return weighted_hours / total_weight
    
    def calculate_scenarios(self, manual_hours_per_sprint: Optional[float] = None) -> Dict:
        """
        Berechnet Best/Realistic/Worst Case Szenarien.
        
        Args:
            manual_hours_per_sprint: Optional manuelle Überschreibung
            
        Returns:
            Dict mit Szenarien und Konfidenzintervallen
        """
        # Automatischer Forecast als Basis
        auto_hours_per_sprint = self.calculate_weighted_sprint_average()
        
        # Nutze manuellen Wert falls vorhanden (None-Check statt truthy für 0.0 Support)
        base_hours = manual_hours_per_sprint if manual_hours_per_sprint is not None else auto_hours_per_sprint
        
        # Berechne Varianz aus historischen Daten
        if self.sprint_data is not None and len(self.sprint_data) >= 2:
            sprint_variance = self.sprint_data['hours'].std()
            confidence_factor = sprint_variance / base_hours if base_hours > 0 else 0.2
        else:
            confidence_factor = 0.2  # Default 20% Unsicherheit
        
        # Verbleibende Stunden
        total_booked = self.bookings_df['Stunden'].sum()
        remaining_hours = max(0, self.target_hours - total_booked)
        
        # Szenarien berechnen
        scenarios = {
            'optimistic': {
                'label': 'Optimistisch (90% Konfidenz)',
                'hours_per_sprint': base_hours * (1 + confidence_factor * 1.5),  # +1.5 Sigma
                'sprints_remaining': None,
                'end_date': None,
                'description': 'Team arbeitet überdurchschnittlich produktiv'
            },
            'realistic': {
                'label': 'Realistisch (50% Konfidenz)',
                'hours_per_sprint': base_hours,
                'sprints_remaining': None,
                'end_date': None,
                'description': 'Fortsetzung des aktuellen Trends'
            },
            'pessimistic': {
                'label': 'Pessimistisch (10% Konfidenz)',
                'hours_per_sprint': max(base_hours * (1 - confidence_factor * 1.5), 0.1),  # -1.5 Sigma
                'sprints_remaining': None,
                'end_date': None,
                'description': 'Verzögerungen, Urlaube, Blocker'
            }
        }
        
        # Berechne Ende-Datum für jedes Szenario
        for scenario_key, scenario in scenarios.items():
            hours_per_sprint = scenario['hours_per_sprint']
            
            if hours_per_sprint > 0:
                sprints_remaining = remaining_hours / hours_per_sprint
                days_remaining = sprints_remaining * SPRINT_DURATION_DAYS
                end_date = self.today + timedelta(days=days_remaining)
                
                scenario['sprints_remaining'] = sprints_remaining
                scenario['end_date'] = end_date
            else:
                scenario['sprints_remaining'] = float('inf')
                scenario['end_date'] = None
        
        return {
            'scenarios': scenarios,
            'base_hours_per_sprint': base_hours,
            'automatic_hours_per_sprint': auto_hours_per_sprint,
            'confidence_factor': confidence_factor,
            'remaining_hours': remaining_hours,
            'total_booked': total_booked,
            'sprint_data': self.sprint_data
        }
    
    def get_sprint_velocity_trend(self) -> Dict:
        """
        Analysiert ob Sprint-Velocity steigt oder fällt.
        
        Returns:
            Dict mit Trend-Information
        """
        if self.sprint_data is None or len(self.sprint_data) < 2:
            return {'trend': 'insufficient_data', 'direction': 0, 'slope': 0}
        
        # Linear Regression über Sprint-Nummern (einfache Implementierung ohne sklearn)
        X = self.sprint_data['sprint_number'].values
        y = self.sprint_data['hours'].values
        
        # Einfache lineare Regression: y = mx + b
        n = len(X)
        x_mean = X.mean()
        y_mean = y.mean()
        
        # Slope berechnen
        numerator = ((X - x_mean) * (y - y_mean)).sum()
        denominator = ((X - x_mean) ** 2).sum()
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Klassifiziere Trend
        if slope > 2:
            trend = 'increasing'
        elif slope < -2:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'slope': slope,
            'direction': np.sign(slope)
        }


def load_forecast_overrides(project_id: str, activity: str = None) -> Optional[Dict]:
    """
    Lädt manuelle Forecast-Overrides aus Cache.
    
    Args:
        project_id: Projekt-ID
        activity: Optional Activity-Name
        
    Returns:
        Dict mit Overrides oder None
    """
    cache_file = f"cache/forecast_{project_id}{'_' + activity if activity else ''}.json"
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
            # Rückwärtskompatibel: default active=True
            if 'active' not in data:
                data['active'] = True
            return data
    except Exception:
        return None


def save_forecast_overrides(
    project_id: str, 
    hours_per_sprint: float,
    reason: str,
    user_email: str,
    activity: str = None,
    active: bool = True
):
    """
    Speichert manuelle Forecast-Overrides.
    
    Args:
        project_id: Projekt-ID
        hours_per_sprint: Erwartete Stunden pro Sprint
        reason: Begründung für Override
        user_email: Benutzer der Override erstellt hat
        activity: Optional Activity-Name
        active: Ob Override aktiv ist (False wenn Benutzer auf Auto zurückschaltet)
    """
    cache_file = f"cache/forecast_{project_id}{'_' + activity if activity else ''}.json"
    
    data = {
        'hours_per_sprint': hours_per_sprint,
        'reason': reason,
        'updated_at': datetime.now().isoformat(),
        'updated_by': user_email,
        'active': active
    }
    
    os.makedirs('cache', exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)
