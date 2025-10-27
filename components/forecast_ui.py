"""
Streamlit UI für Forecast-Management
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import Optional
from utils.forecast_engine import (
    ForecastEngine, 
    load_forecast_overrides, 
    save_forecast_overrides
)

def render_forecast_scenarios(
    project_id: str,
    bookings_df: pd.DataFrame,
    target_hours: float,
    user_email: str,
    activity: str = None
) -> None:
    """
    Rendert Forecast-Szenarien mit manueller Override-Option.
    
    Args:
        project_id: Projekt-ID
        bookings_df: Buchungsdaten
        target_hours: Sollstunden
        user_email: Aktueller Benutzer
        activity: Optional Activity-Name
    """
    st.subheader("🔮 Budget-Prognose mit Szenarien")
    
    if target_hours <= 0:
        st.warning("⚠️ Bitte setzen Sie erst Sollstunden im Tab 'Übersicht', um Prognosen zu berechnen.")
        return
    
    if bookings_df.empty:
        st.info("ℹ️ Noch keine Buchungen vorhanden. Prognose wird nach ersten Buchungen verfügbar.")
        return
    
    # Forecast Engine initialisieren
    engine = ForecastEngine(bookings_df, target_hours)
    
    # Lade existierende Overrides
    overrides = load_forecast_overrides(project_id, activity)
    
    # Session State Keys (Single Source of Truth)
    key_suffix = f"{project_id}{'_' + activity if activity else ''}"
    k_use = f"mf_use_{key_suffix}"
    k_hours = f"mf_hours_{key_suffix}"
    k_reason = f"mf_reason_{key_suffix}"
    
    # Initialisiere Session State wenn noch nicht vorhanden
    auto_value = engine.calculate_weighted_sprint_average()
    
    if k_use not in st.session_state:
        st.session_state[k_use] = bool(overrides and overrides.get('active', True))
    
    if k_hours not in st.session_state:
        st.session_state[k_hours] = float(overrides['hours_per_sprint']) if (overrides and overrides.get('active', True)) else float(auto_value)
    
    if k_reason not in st.session_state:
        st.session_state[k_reason] = overrides['reason'] if overrides else ""
    
    # UI für manuelle Anpassungen
    col1, col2 = st.columns([2, 1])
    
    with col1:
        use_manual = st.checkbox(
            "📝 Manuelle Prognose aktivieren",
            value=st.session_state[k_use],
            help="Überschreibe automatische Berechnung mit eigener Einschätzung",
            key=k_use
        )
    
    manual_hours_per_sprint = None
    override_reason = st.session_state[k_reason]
    
    if use_manual:
        with col2:
            manual_hours_per_sprint = st.number_input(
                "Erwartete Std/Sprint (2 Wochen):",
                min_value=0.0,
                value=st.session_state[k_hours],
                step=5.0,
                help="Basierend auf geplanten Kapazitäten, Team-Größe, etc.",
                key=k_hours
            )
        
        reason_col, save_col = st.columns([3, 1])
        with reason_col:
            override_reason = st.text_input(
                "Begründung:",
                value=st.session_state[k_reason],
                placeholder="z.B. 'Neuer Entwickler ab Oktober' oder 'Team-Urlaub geplant'",
                key=k_reason
            )
        
        with save_col:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("💾 Speichern", width='stretch', key=f"save_btn_{key_suffix}"):
                save_forecast_overrides(
                    project_id, 
                    st.session_state[k_hours], 
                    st.session_state[k_reason],
                    user_email,
                    activity,
                    active=st.session_state[k_use]
                )
                st.success("Prognose gespeichert!")
                st.rerun()
    
    # Berechne Szenarien mit aktivem Wert aus Session State
    active_hours = st.session_state[k_hours] if st.session_state[k_use] else None
    forecast_result = engine.calculate_scenarios(active_hours)
    
    # Sprint-Velocity Trend
    velocity_trend = engine.get_sprint_velocity_trend()
    
    # Zeige Trend-Warnung
    if velocity_trend['trend'] == 'decreasing':
        st.warning(f"⚠️ **Trend-Warnung:** Sprint-Velocity nimmt ab ({velocity_trend['slope']:.1f}h/Sprint). "
                  f"Team könnte überlastet sein oder auf Blocker stoßen.")
    elif velocity_trend['trend'] == 'increasing':
        st.info(f"📈 **Positiver Trend:** Sprint-Velocity steigt ({velocity_trend['slope']:.1f}h/Sprint). "
               f"Team wird produktiver!")
    
    # Scenario Cards
    st.write("### Prognose-Szenarien")
    
    scenarios = forecast_result['scenarios']
    cols = st.columns(3)
    
    colors = {
        'optimistic': '🟢',
        'realistic': '🟡', 
        'pessimistic': '🔴'
    }
    
    for idx, (key, scenario) in enumerate(scenarios.items()):
        with cols[idx]:
            color_icon = colors[key]
            
            st.markdown(f"#### {color_icon} {scenario['label']}")
            
            if scenario['end_date']:
                days_remaining = (scenario['end_date'] - engine.today).days
                st.metric(
                    "Budget-Ende",
                    scenario['end_date'].strftime("%d.%m.%Y"),
                    delta=f"{days_remaining} Tage"
                )
                
                st.caption(f"📅 {scenario['sprints_remaining']:.1f} Sprints verbleibend")
                st.caption(f"⚡ {scenario['hours_per_sprint']:.1f}h/Sprint")
            else:
                st.metric("Budget-Ende", "Unbekannt")
            
            with st.expander("Details"):
                st.write(scenario['description'])
                if scenario['sprints_remaining']:
                    st.write(f"**Sprints verbleibend:** {scenario['sprints_remaining']:.2f}")
                    st.write(f"**Stunden/Sprint:** {scenario['hours_per_sprint']:.1f}h")
    
    # Zusätzliche Metriken
    st.divider()
    
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric(
            "Basis-Velocity",
            f"{forecast_result['base_hours_per_sprint']:.1f}h/Sprint",
            help="Gewichteter Durchschnitt der letzten 4 Sprints"
        )
    with metric_cols[1]:
        st.metric(
            "Verbleibende Stunden",
            f"{forecast_result['remaining_hours']:.1f}h",
            delta=f"-{forecast_result['total_booked']:.1f}h gebucht"
        )
    with metric_cols[2]:
        auslastung = (forecast_result['total_booked'] / target_hours * 100) if target_hours > 0 else 0
        st.metric(
            "Auslastung",
            f"{auslastung:.1f}%"
        )
    with metric_cols[3]:
        confidence_pct = max(0, min(100, (1 - forecast_result['confidence_factor']) * 100))
        st.metric(
            "Prognose-Sicherheit",
            f"{confidence_pct:.0f}%",
            help="Basierend auf Varianz der historischen Sprint-Daten"
        )
    
    # Sprint-Daten Tabelle (expandable)
    with st.expander("📊 Sprint-Details anzeigen"):
        if len(engine.sprint_data) > 0:
            sprint_display = engine.sprint_data.copy()
            sprint_display['sprint_label'] = sprint_display['sprint_number'].apply(
                lambda x: f"Sprint -{x}" if x > 0 else "Aktueller Sprint"
            )
            sprint_display['sprint_start'] = pd.to_datetime(sprint_display['sprint_start']).dt.strftime('%d.%m.%Y')
            sprint_display['sprint_end'] = pd.to_datetime(sprint_display['sprint_end']).dt.strftime('%d.%m.%Y')
            sprint_display['weight_pct'] = sprint_display['weight'].apply(lambda x: f"{x*100:.0f}%")
            sprint_display['hours_formatted'] = sprint_display['hours'].apply(lambda x: f"{x:.1f}h")
            
            display_df = sprint_display[['sprint_label', 'hours_formatted', 'sprint_start', 'sprint_end', 'weight_pct']]
            display_df.columns = ['Sprint', 'Stunden', 'Start', 'Ende', 'Gewicht']
            st.dataframe(display_df, width='stretch', hide_index=True)
        else:
            st.info("Noch keine Sprint-Daten verfügbar (benötigt Buchungen der letzten 8 Wochen)")
    
    # Hinweis bei manueller Override
    if overrides and overrides.get('active', True):
        st.info(f"ℹ️ **Manuelle Prognose aktiv** (seit {overrides['updated_at'][:10]}): "
               f"_{overrides['reason']}_")
    
    # Gebe aktiven Wert zurück für Chart-Rendering
    return active_hours


def render_scenario_chart(
    project_id: str,
    bookings_df: pd.DataFrame,
    target_hours: float,
    activity: str = None,
    manual_hours_per_sprint: Optional[float] = None,
    use_manual: Optional[bool] = None
) -> None:
    """
    Visualisiert Szenarien als Burn-down Chart mit 3 Linien.
    
    Args:
        project_id: Projekt-ID
        bookings_df: Buchungsdaten
        target_hours: Sollstunden
        activity: Optional Activity-Name
        manual_hours_per_sprint: Optional aktiver manueller Wert aus UI
        use_manual: Optional ob manuelle Prognose aktiv ist
    """
    if bookings_df.empty or target_hours <= 0:
        return
    
    # Ermittele aktiven Wert (Single Source of Truth aus Session State)
    key_suffix = f"{project_id}{'_' + activity if activity else ''}"
    k_use = f"mf_use_{key_suffix}"
    k_hours = f"mf_hours_{key_suffix}"
    
    # Prüfe Session State zuerst
    if use_manual is None:
        use_manual = st.session_state.get(k_use, None)
    
    if manual_hours_per_sprint is None:
        manual_hours_per_sprint = st.session_state.get(k_hours, None)
    
    # Falls Session State leer, versuche gespeicherte Overrides
    if use_manual is None or manual_hours_per_sprint is None:
        overrides = load_forecast_overrides(project_id, activity)
        if overrides:
            if use_manual is None:
                use_manual = overrides.get('active', True)
            if manual_hours_per_sprint is None:
                manual_hours_per_sprint = overrides['hours_per_sprint']
    
    # Bestimme aktiven Wert für Berechnung
    active_hours = manual_hours_per_sprint if use_manual else None
    
    engine = ForecastEngine(bookings_df, target_hours)
    forecast_result = engine.calculate_scenarios(active_hours)
    scenarios = forecast_result['scenarios']
    
    # Historische Daten
    bookings_df['DatumBuchung'] = pd.to_datetime(bookings_df['DatumBuchung'])
    daily_data = bookings_df.groupby('DatumBuchung')['Stunden'].sum().reset_index()
    daily_data = daily_data.sort_values('DatumBuchung')
    daily_data['Stunden_kumuliert'] = daily_data['Stunden'].cumsum()
    
    # Plotly Figure
    fig = go.Figure()
    
    # 1. Sollstunden (horizontal)
    max_date = max([s['end_date'] for s in scenarios.values() if s['end_date']], default=daily_data['DatumBuchung'].max())
    
    fig.add_trace(go.Scatter(
        x=[daily_data['DatumBuchung'].min(), max_date],
        y=[target_hours, target_hours],
        name='Sollstunden (Budget)',
        line=dict(dash='dash', color='gray', width=2),
        mode='lines',
        hovertemplate='Sollstunden: %{y:.1f}h<extra></extra>'
    ))
    
    # 2. Ist-Stunden (historisch)
    current_hours = daily_data['Stunden_kumuliert'].iloc[-1] if len(daily_data) > 0 else 0
    
    fig.add_trace(go.Scatter(
        x=daily_data['DatumBuchung'],
        y=daily_data['Stunden_kumuliert'],
        name='Ist-Stunden (kumuliert)',
        line=dict(color='steelblue', width=3),
        fill='tozeroy',
        fillcolor='rgba(70,130,180,0.1)',
        mode='lines',
        hovertemplate='%{x|%d.%m.%Y}<br>Kumuliert: %{y:.1f}h<extra></extra>'
    ))
    
    # 3. Forecast-Linien (alle 3 Szenarien)
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
    
    today = engine.today
    
    for key, scenario in scenarios.items():
        if scenario['end_date']:
            fig.add_trace(go.Scatter(
                x=[today, scenario['end_date']],
                y=[current_hours, target_hours],
                name=scenario['label'],
                line=dict(dash=scenario_dash[key], color=scenario_colors[key], width=2),
                mode='lines',
                hovertemplate=f"{scenario['label']}<br>%{{x|%d.%m.%Y}}<br>%{{y:.1f}}h<extra></extra>"
            ))
            
            # Ende-Marker
            fig.add_trace(go.Scatter(
                x=[scenario['end_date']],
                y=[target_hours],
                name=f"{key} Ende",
                mode='markers',
                marker=dict(size=10, color=scenario_colors[key], symbol='x'),
                showlegend=False,
                hovertemplate=f"{scenario['label']}<br>%{{x|%d.%m.%Y}}<extra></extra>"
            ))
    
    # Layout
    fig.update_layout(
        title=f"Burn-down mit Szenarien: {project_id}",
        xaxis_title="Datum",
        yaxis_title="Stunden (kumuliert)",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    
    st.plotly_chart(fig, width='stretch')


def render_sprint_velocity_chart(sprint_data: pd.DataFrame) -> None:
    """
    Zeigt Sprint-Velocity als Balkendiagramm mit Gewichtung.
    
    Args:
        sprint_data: DataFrame mit Sprint-Informationen
    """
    if sprint_data.empty:
        st.info("Keine Sprint-Daten verfügbar")
        return
    
    st.write("### Sprint-Velocity Analyse")
    
    fig = go.Figure()
    
    # Sprint-Labels
    sprint_data['sprint_label'] = sprint_data['sprint_number'].apply(
        lambda x: f"Sprint -{x}" if x > 0 else "Aktuell"
    )
    
    # Balken mit Gewichtungs-Einfärbung
    colors = ['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a']  # Hell zu Dunkel
    bar_colors = [colors[min(int(w * 10), 3)] for w in sprint_data['weight']]
    
    fig.add_trace(go.Bar(
        x=sprint_data['sprint_label'],
        y=sprint_data['hours'],
        name='Stunden/Sprint',
        marker_color=bar_colors,
        text=sprint_data['hours'].apply(lambda x: f"{x:.1f}h"),
        textposition='outside',
        hovertemplate='%{x}<br>Stunden: %{y:.1f}h<br>Gewicht: %{customdata}<extra></extra>',
        customdata=sprint_data['weight'].apply(lambda x: f"{x*100:.0f}%")
    ))
    
    # Gewichteter Durchschnitt als Linie
    avg_weighted = (sprint_data['hours'] * sprint_data['weight']).sum() / sprint_data['weight'].sum()
    
    fig.add_hline(
        y=avg_weighted,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Gewichteter Ø: {avg_weighted:.1f}h",
        annotation_position="right"
    )
    
    fig.update_layout(
        title="Sprint-Velocity (gewichtet)",
        xaxis_title="Sprint",
        yaxis_title="Gebuchte Stunden",
        showlegend=False,
        height=350
    )
    
    st.plotly_chart(fig, width='stretch')
