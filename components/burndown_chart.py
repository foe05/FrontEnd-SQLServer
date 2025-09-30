"""
Burn-down Charts and time series visualizations
"""
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

def calculate_project_timeline(bookings_df: pd.DataFrame, target_hours: float) -> Dict[str, Optional[datetime]]:
    """
    Berechnet Projekt-Timeline aus Buchungsdaten.
    
    Args:
        bookings_df: DataFrame mit Spalten [DatumBuchung, Stunden]
        target_hours: Sollstunden aus Cache
        
    Returns:
        dict mit 'start_date', 'end_date', 'forecast_end'
    """
    if bookings_df.empty:
        return {
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=30),
            'forecast_end': None
        }
    
    # Projektstart: Frühestes DatumBuchung
    start_date = pd.to_datetime(bookings_df['DatumBuchung']).min()
    
    # Projektende: Spätestes DatumBuchung + 30 Tage Buffer
    end_date = pd.to_datetime(bookings_df['DatumBuchung']).max() + timedelta(days=30)
    
    # Forecast basierend auf letzten 4 Wochen
    forecast_end = calculate_budget_forecast(bookings_df, target_hours)
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'forecast_end': forecast_end
    }

def calculate_budget_forecast(bookings_df: pd.DataFrame, target_hours: float) -> Optional[datetime]:
    """
    Prognostiziert Budget-Ende basierend auf durchschnittlicher Buchungsrate der letzten 4 Wochen.
    
    Args:
        bookings_df: DataFrame mit [DatumBuchung, Stunden]
        target_hours: Verbleibende Sollstunden
        
    Returns:
        Prognostiziertes Datum der Budget-Erschöpfung oder None
    """
    if bookings_df.empty or target_hours <= 0:
        return None
    
    # Letzte 4 Wochen filtern
    four_weeks_ago = datetime.now() - timedelta(weeks=4)
    bookings_df['DatumBuchung'] = pd.to_datetime(bookings_df['DatumBuchung'])
    recent_bookings = bookings_df[bookings_df['DatumBuchung'] >= four_weeks_ago]
    
    if len(recent_bookings) == 0:
        return None
    
    # Durchschnitt Stunden/Woche
    total_hours_recent = recent_bookings['Stunden'].sum()
    date_span = (recent_bookings['DatumBuchung'].max() - recent_bookings['DatumBuchung'].min()).days
    weeks_span = max(date_span / 7, 1)
    avg_hours_per_week = total_hours_recent / weeks_span
    
    # Verbleibende Stunden
    total_booked = bookings_df['Stunden'].sum()
    remaining_hours = target_hours - total_booked
    
    # Prognose
    if avg_hours_per_week > 0 and remaining_hours > 0:
        weeks_remaining = remaining_hours / avg_hours_per_week
        forecast_date = datetime.now() + timedelta(weeks=weeks_remaining)
        return forecast_date
    elif remaining_hours <= 0:
        # Budget bereits erschöpft
        return datetime.now()
    
    return None

def render_burndown_chart(
    project_id: str,
    bookings_df: pd.DataFrame, 
    target_hours: float,
    level: str = "project",
    show_scenarios: bool = True,
    activity: str = None
) -> None:
    """
    Rendert interaktiven Burn-down Chart mit Plotly und Szenarien.
    
    Args:
        project_id: Projekt-ID für Titel
        bookings_df: DataFrame mit [DatumBuchung, Stunden]
        target_hours: Sollstunden aus Cache
        level: "project" oder "activity"
        show_scenarios: Wenn True, zeige 3 Prognose-Szenarien
    
    Features:
    - Sollstunden-Linie (konstant über Projektlaufzeit)
    - Ist-Stunden kumuliert (aus Buchungen)
    - 3 Forecast-Szenarien (optimistisch/realistisch/pessimistisch)
    - Status-Färbung (Grün/Gelb/Rot)
    - Budget-Ende-Datum prominent angezeigt
    """
    
    if bookings_df.empty:
        st.warning(f"Keine Buchungsdaten verfügbar für {project_id}")
        return
    
    # Timeline berechnen
    timeline = calculate_project_timeline(bookings_df, target_hours)
    
    # Daten vorbereiten
    bookings_df['DatumBuchung'] = pd.to_datetime(bookings_df['DatumBuchung'])
    daily_data = bookings_df.groupby('DatumBuchung')['Stunden'].sum().reset_index()
    daily_data = daily_data.sort_values('DatumBuchung')
    daily_data['Stunden_kumuliert'] = daily_data['Stunden'].cumsum()
    
    # Plotly Figure erstellen
    fig = go.Figure()
    
    # 1. Sollstunden-Linie (horizontal)
    fig.add_trace(go.Scatter(
        x=[timeline['start_date'], timeline['end_date']],
        y=[target_hours, target_hours],
        name='Sollstunden (Budget)',
        line=dict(dash='dash', color='gray', width=2),
        mode='lines',
        hovertemplate='Sollstunden: %{y:.1f}h<extra></extra>'
    ))
    
    # 2. Ist-Stunden kumuliert
    current_hours = daily_data['Stunden_kumuliert'].iloc[-1] if len(daily_data) > 0 else 0
    
    # Status-Farbe bestimmen
    if target_hours > 0:
        fulfillment_pct = (current_hours / target_hours) * 100
        if fulfillment_pct <= 100:
            status_color = 'green'
        elif fulfillment_pct <= 110:
            status_color = 'orange'
        else:
            status_color = 'red'
    else:
        status_color = 'blue'
    
    # Color mapping für Fill
    color_map = {
        "green": "0,255,0",
        "orange": "255,165,0", 
        "red": "255,0,0",
        "blue": "0,0,255"
    }
    rgb_color = color_map.get(status_color, "128,128,128")
    
    fig.add_trace(go.Scatter(
        x=daily_data['DatumBuchung'],
        y=daily_data['Stunden_kumuliert'],
        name='Ist-Stunden (kumuliert)',
        line=dict(color=status_color, width=3),
        fill='tozeroy',
        fillcolor=f'rgba({rgb_color},0.1)',
        mode='lines+markers',
        hovertemplate='Datum: %{x|%d.%m.%Y}<br>Kumuliert: %{y:.1f}h<extra></extra>'
    ))
    
    # 3. Forecast-Szenarien (Sprint-basiert)
    if show_scenarios and target_hours > 0:
        from utils.forecast_engine import ForecastEngine, load_forecast_overrides
        
        try:
            # Lade Override falls vorhanden (wichtig für Chart-Update)
            # Bei Activity-Level wird auch der Activity-Name benötigt
            overrides = load_forecast_overrides(project_id, activity)
            manual_hours = overrides['hours_per_sprint'] if overrides else None
            
            engine = ForecastEngine(bookings_df, target_hours)
            forecast_result = engine.calculate_scenarios(manual_hours)
            scenarios = forecast_result['scenarios']
            
            scenario_colors = {
                'optimistic': 'green',
                'realistic': 'orange',
                'pessimistic': 'red'
            }
            
            scenario_dash = {
                'optimistic': 'dot',
                'realistic': 'solid',
                'pessimistic': 'dot'
            }
            
            today = datetime.now()
            
            for key, scenario in scenarios.items():
                if scenario['end_date'] and scenario['end_date'] > today:
                    fig.add_trace(go.Scatter(
                        x=[today, scenario['end_date']],
                        y=[current_hours, target_hours],
                        name=scenario['label'],
                        line=dict(dash=scenario_dash[key], color=scenario_colors[key], width=2),
                        mode='lines',
                        hovertemplate=f"{scenario['label']}<br>%{{x|%d.%m.%Y}}<br>%{{y:.1f}}h<extra></extra>"
                    ))
                    
                    # Ende-Marker für realistisches Szenario
                    if key == 'realistic':
                        fig.add_trace(go.Scatter(
                            x=[scenario['end_date']],
                            y=[target_hours],
                            name='Budget-Ende (realistisch)',
                            mode='markers',
                            marker=dict(size=12, color='orange', symbol='x'),
                            showlegend=False,
                            hovertemplate=f"Budget-Ende: %{{x|%d.%m.%Y}}<extra></extra>"
                        ))
        except Exception as e:
            # Fallback auf einfache Prognose
            if timeline['forecast_end'] and target_hours > current_hours:
                fig.add_trace(go.Scatter(
                    x=[datetime.now(), timeline['forecast_end']],
                    y=[current_hours, target_hours],
                    name='Prognose (4-Wochen-Trend)',
                    line=dict(dash='dot', color='orange', width=2),
                    mode='lines',
                    hovertemplate='Prognose: %{y:.1f}h<br>Datum: %{x|%d.%m.%Y}<extra></extra>'
                ))
    
    # Layout
    fig.update_layout(
        title=f"Burn-down Chart: {project_id}",
        xaxis_title="Datum",
        yaxis_title="Stunden (kumuliert)",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    
    # Render in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
    # Metriken unterhalb des Charts
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sollstunden", f"{target_hours:.1f} h")
    
    with col2:
        delta_hours = current_hours - target_hours
        st.metric("Ist-Stunden", f"{current_hours:.1f} h", 
                 delta=f"{delta_hours:+.1f} h",
                 delta_color="inverse")
    
    with col3:
        if target_hours > 0:
            fulfillment_pct = (current_hours / target_hours) * 100
            st.metric("Erfüllungsstand", f"{fulfillment_pct:.1f}%")
        else:
            st.metric("Erfüllungsstand", "N/A")
    
    with col4:
        if timeline['forecast_end'] and target_hours > current_hours:
            days_remaining = (timeline['forecast_end'] - datetime.now()).days
            st.metric("Budget-Ende (Prognose)", 
                     timeline['forecast_end'].strftime("%d.%m.%Y"),
                     delta=f"{days_remaining} Tage")
        elif target_hours <= current_hours:
            st.metric("Budget-Status", "⚠️ Erschöpft")
        else:
            st.metric("Budget-Ende", "Keine Prognose")

def render_weekly_trend(bookings_df: pd.DataFrame, project_id: str) -> None:
    """
    Zeigt gebuchte Stunden pro Woche als Balkendiagramm.
    
    Args:
        bookings_df: DataFrame mit [DatumBuchung, Stunden]
        project_id: Projekt-ID für Titel
    """
    if bookings_df.empty:
        st.info("Keine Daten für Wochentrend verfügbar")
        return
    
    # Datum konvertieren
    bookings_df['DatumBuchung'] = pd.to_datetime(bookings_df['DatumBuchung'])
    
    # Wochenaggregation
    bookings_df['Woche'] = bookings_df['DatumBuchung'].dt.to_period('W')
    weekly_data = bookings_df.groupby('Woche')['Stunden'].sum().reset_index()
    weekly_data['Woche_Start'] = weekly_data['Woche'].dt.start_time
    
    # Plotly Bar Chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=weekly_data['Woche_Start'],
        y=weekly_data['Stunden'],
        name='Wochenstunden',
        marker_color='steelblue',
        hovertemplate='KW %{x|%W/%Y}<br>Stunden: %{y:.1f}h<extra></extra>'
    ))
    
    # 4-Wochen-Durchschnitt als Linie
    if len(weekly_data) >= 4:
        avg_4weeks = weekly_data.tail(4)['Stunden'].mean()
        fig.add_hline(y=avg_4weeks, line_dash="dash", 
                      annotation_text=f"Ø letzte 4 Wochen: {avg_4weeks:.1f}h",
                      line_color="orange")
    
    # Gesamtdurchschnitt
    avg_total = weekly_data['Stunden'].mean()
    fig.add_hline(y=avg_total, line_dash="dot", 
                  annotation_text=f"Ø Gesamt: {avg_total:.1f}h",
                  line_color="green")
    
    fig.update_layout(
        title=f"Wochentrend: {project_id}",
        xaxis_title="Kalenderwoche",
        yaxis_title="Gebuchte Stunden",
        showlegend=True,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Metriken
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Wochen gesamt", len(weekly_data))
    
    with col2:
        st.metric("Ø Stunden/Woche", f"{avg_total:.1f} h")
    
    with col3:
        if len(weekly_data) >= 4:
            st.metric("Ø letzte 4 Wochen", f"{avg_4weeks:.1f} h")
        else:
            st.metric("Ø letzte 4 Wochen", "N/A")

def render_activity_comparison(bookings_df: pd.DataFrame, project_id: str) -> None:
    """
    Zeigt zeitlichen Verlauf verschiedener Activities im Vergleich.
    
    Args:
        bookings_df: DataFrame mit [DatumBuchung, Activity, Stunden]
        project_id: Projekt-ID für Titel
    """
    if bookings_df.empty or 'Activity' not in bookings_df.columns:
        st.info("Keine Activity-Daten für Vergleich verfügbar")
        return
    
    # Datum konvertieren
    bookings_df['DatumBuchung'] = pd.to_datetime(bookings_df['DatumBuchung'])
    
    # Wochenweise Aggregation pro Activity
    bookings_df['Woche'] = bookings_df['DatumBuchung'].dt.to_period('W')
    
    activity_weekly = bookings_df.groupby(['Woche', 'Activity'])['Stunden'].sum().reset_index()
    activity_weekly['Woche_Start'] = activity_weekly['Woche'].dt.start_time
    
    # Plotly Stacked Bar Chart
    fig = go.Figure()
    
    activities = activity_weekly['Activity'].unique()
    colors = ['#0066cc', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dfe6e9']
    
    for idx, activity in enumerate(activities):
        activity_data = activity_weekly[activity_weekly['Activity'] == activity]
        
        fig.add_trace(go.Bar(
            x=activity_data['Woche_Start'],
            y=activity_data['Stunden'],
            name=activity,
            marker_color=colors[idx % len(colors)],
            hovertemplate=f'{activity}<br>KW %{{x|%W/%Y}}<br>%{{y:.1f}}h<extra></extra>'
        ))
    
    fig.update_layout(
        title=f"Activity-Vergleich über Zeit: {project_id}",
        xaxis_title="Kalenderwoche",
        yaxis_title="Gebuchte Stunden",
        barmode='stack',
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_cumulative_comparison(bookings_df: pd.DataFrame, target_hours_by_activity: Dict[str, float]) -> None:
    """
    Zeigt kumulative Stunden pro Activity mit Soll-Linien.
    
    Args:
        bookings_df: DataFrame mit [DatumBuchung, Activity, Stunden]
        target_hours_by_activity: Dict {activity_name: target_hours}
    """
    if bookings_df.empty or 'Activity' not in bookings_df.columns:
        st.info("Keine Activity-Daten verfügbar")
        return
    
    # Datum konvertieren
    bookings_df['DatumBuchung'] = pd.to_datetime(bookings_df['DatumBuchung'])
    
    fig = go.Figure()
    
    activities = bookings_df['Activity'].unique()
    colors = ['#0066cc', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
    
    for idx, activity in enumerate(activities):
        activity_data = bookings_df[bookings_df['Activity'] == activity].sort_values('DatumBuchung')
        activity_data['Kumuliert'] = activity_data['Stunden'].cumsum()
        
        # Kumulative Linie
        fig.add_trace(go.Scatter(
            x=activity_data['DatumBuchung'],
            y=activity_data['Kumuliert'],
            name=activity,
            line=dict(color=colors[idx % len(colors)], width=2),
            mode='lines+markers',
            hovertemplate=f'{activity}<br>%{{x|%d.%m.%Y}}<br>Kumuliert: %{{y:.1f}}h<extra></extra>'
        ))
        
        # Sollstunden-Linie (wenn vorhanden)
        target = target_hours_by_activity.get(activity, 0)
        if target > 0:
            fig.add_trace(go.Scatter(
                x=[activity_data['DatumBuchung'].min(), activity_data['DatumBuchung'].max()],
                y=[target, target],
                name=f'{activity} (Soll)',
                line=dict(dash='dash', color=colors[idx % len(colors)], width=1),
                mode='lines',
                showlegend=False,
                hovertemplate=f'{activity} Soll: %{{y:.1f}}h<extra></extra>'
            ))
    
    fig.update_layout(
        title="Kumulative Stunden pro Activity",
        xaxis_title="Datum",
        yaxis_title="Stunden (kumuliert)",
        hovermode='x unified',
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_forecast_metrics(bookings_df: pd.DataFrame, target_hours: float) -> None:
    """
    Zeigt Prognose-Metriken in kompakter Form.
    
    Args:
        bookings_df: DataFrame mit Buchungsdaten
        target_hours: Sollstunden
    """
    if bookings_df.empty:
        return
    
    st.subheader("📊 Prognose & Trends")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Letzte 4 Wochen Durchschnitt
    four_weeks_ago = datetime.now() - timedelta(weeks=4)
    bookings_df['DatumBuchung'] = pd.to_datetime(bookings_df['DatumBuchung'])
    recent = bookings_df[bookings_df['DatumBuchung'] >= four_weeks_ago]
    
    if len(recent) > 0:
        date_span = (recent['DatumBuchung'].max() - recent['DatumBuchung'].min()).days
        weeks = max(date_span / 7, 1)
        avg_per_week = recent['Stunden'].sum() / weeks
    else:
        avg_per_week = 0
    
    with col1:
        st.metric("Ø Stunden/Woche (4W)", f"{avg_per_week:.1f} h")
    
    # Gesamtdurchschnitt
    total_span = (bookings_df['DatumBuchung'].max() - bookings_df['DatumBuchung'].min()).days
    total_weeks = max(total_span / 7, 1)
    total_avg = bookings_df['Stunden'].sum() / total_weeks
    
    with col2:
        st.metric("Ø Stunden/Woche (Gesamt)", f"{total_avg:.1f} h")
    
    # Verbleibende Stunden
    total_booked = bookings_df['Stunden'].sum()
    remaining = target_hours - total_booked
    
    with col3:
        st.metric("Verbleibende Stunden", f"{remaining:.1f} h",
                 delta=f"{(remaining/target_hours*100):.1f}%" if target_hours > 0 else None)
    
    # Prognose Wochen
    if avg_per_week > 0 and remaining > 0:
        weeks_remaining = remaining / avg_per_week
        with col4:
            st.metric("Wochen bis Budget-Ende", f"{weeks_remaining:.1f}")
    else:
        with col4:
            if remaining <= 0:
                st.metric("Budget-Status", "Erschöpft", delta_color="off")
            else:
                st.metric("Budget-Status", "Keine Aktivität")
