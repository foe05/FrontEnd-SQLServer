# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-30

### Added

#### 🎯 Sprint-basierte Forecasting-Features
- **Sprint-basierte Prognosen** mit gewichteter 4-Sprint-Analyse (40%, 30%, 20%, 10%)
- **3 Prognose-Szenarien**: Optimistisch (90%), Realistisch (50%), Pessimistisch (10%)
- **Budget-Ende-Berechnung** automatisch basierend auf Sprint-Velocity
- **Manuelle Override-Funktion** mit Begründung und Persistierung im Filesystem
- **Velocity-Trend-Analyse** mit automatischen Warnungen bei sinkender Produktivität
- **Prognose-Sicherheit** Metrik basierend auf historischer Varianz

#### 📊 Visualisierungen
- **Burn-down Charts** mit Plotly und 3 farbigen Szenario-Linien
- **Sprint-Velocity Charts** für Deep-Dive in Team-Performance
- **Wochentrend-Charts** mit 4-Wochen-Durchschnitt
- **Activity-Vergleichs-Charts** über Zeit
- **Szenario-Visualisierung** im integrierten Burn-down Chart

#### 🎨 UI/UX-Verbesserungen
- **Tab-Navigation**: Übersicht | Zeitreihen | Export
- **Live-Updates**: Alle Charts und Metriken aktualisieren sofort bei Änderungen
- **Session State Management** für konsistente UI-Updates
- **Activity-Level Forecasts** für detaillierte Planung
- **Expandable Sprint-Details** Tabelle mit Gewichtungen

#### 🧪 TEST-Mode Erweiterungen
- **Aktuelle Dummy-Daten** (letzte 8 Wochen bis heute)
- **Sprint-basierte Dummy-Generierung** mit realistischer Velocity-Variation
- **Werktage-Filter** (nur Mo-Fr) für realistische Simulationen
- **Velocity-Varianz** zwischen Sprints (65-95h pro Sprint)

#### 📝 Neue Komponenten
- `components/forecast_ui.py` - Szenario-UI und Visualisierung
- `utils/forecast_engine.py` - Sprint-Berechnungen und Trend-Analyse  
- `components/burndown_chart.py` - Erweiterte Chart-Funktionen
- `SPRINT_FORECAST_FEATURES.md` - Feature-Dokumentation
- `ZEITREIHEN_ANLEITUNG.md` - Benutzer-Anleitung
- `DEPLOYMENT_VERIFICATION.md` - Feature-Parität Matrix

#### 🔧 Basis-Features (bereits in Initial Release)
- **Projekt-Zusammenfassung**: Soll vs. Ist-Stunden pro Projekt
- **Editierbare Sollstunden** mit Default 0
- **Prozentuale Anteile** am Gesamtprojekt
- **Flexible Stunden-Quelle**: Zeit vs. FaktStd Spalten-Auswahl
- **Status-Ampeln**: 🟢 ≤100% | 🟡 100-110% | 🔴 >110%
- **Excel Export** mit Formatierung
- **Entra ID Authentication** mit lokaler Fallback
- **TEST_MODE** mit Auto-Login
- **Docker Support**: Simple/Test/Production Modi
- **Health Monitoring** Dashboard
- **iframe Embedding** für Azure DevOps

### Changed

- **Dummy-Daten Zeitraum**: Von Januar-September 2024 → Letzte 8 Wochen (aktuell)
- **requirements.txt**: plotly==5.17.0 → plotly>=5.18.0
- **requirements.txt**: Hinzugefügt scikit-learn>=1.3.0
- **app.py**: Umstrukturiert mit Tab-Navigation
- **database.py**: Neue Funktion `get_project_bookings()` für Zeitreihen
- **test_database.py**: Sprint-basierte Dummy-Daten-Generierung
- **Dockerfile.test**: Optimiert für neue Dependencies
- **README.md**: Erweitert mit Zeitreihen-Features Dokumentation
- **AGENTS.md**: Architecture-Sektion erweitert

### Fixed

- **Logout-Funktionalität**: Session State wird vollständig geleert
- **OAuth Code Cleanup**: Query-Parameter nach Login entfernt
- **Duplicate Checkbox Keys**: Unique Keys bei mehreren Projekten
- **Auto-Login Loop**: Verhindert durch `_autologin_used` Flag
- **Benutzer wechseln**: Funktioniert jetzt korrekt mit `force_test_user_selection`
- **Streamlit API Exception**: set_page_config() vor allen anderen Streamlit-Befehlen
- **Permission Denied**: Docker Home-Verzeichnis Berechtigungen gefixt
- **pyodbc/msal Optional**: Imports funktionieren auch ohne diese Dependencies
- **iframe Embedding**: CORS aktiviert für Azure DevOps Integration

### Technical Details

**Dependencies:**
```
streamlit>=1.30.0
pandas==2.1.4
plotly>=5.18.0
numpy==1.26.2
scikit-learn>=1.3.0
openpyxl==3.1.2
python-dotenv==1.0.0
requests==2.31.0
pyodbc==5.0.1 (optional, nur Production)
msal==1.25.0 (optional, nur Production)
```

**Architecture:**
- Frontend: Streamlit (Python 3.11+)
- Database: SQL Server (ZV table) mit pyodbc
- Auth: Microsoft Entra ID via msal-python
- Visualization: Plotly for charts
- Forecasting: Custom Sprint-based engine
- Caching: Filesystem-based (JSON)
- Container: Docker multi-stage builds

**Deployment Modes:**
1. **Simple** (Port 8503): Minimale Dependencies, TEST_MODE, schneller Build
2. **Test** (Port 8502): Vollständige Dependencies, TEST_MODE, non-root user
3. **Production** (Port 8501): SQL Server + Entra ID, vollständige Features

---

## Upgrade Instructions

### From Pre-1.0.0 (if exists):

**Lokale Entwicklung:**
```bash
git pull origin main
pip install -r requirements.txt --upgrade
python -m streamlit run app.py
```

**Docker:**
```bash
# Simple Mode
docker-compose -f docker-compose.simple.yml build --no-cache
docker-compose -f docker-compose.simple.yml up -d

# Test Mode
docker-compose -f docker-compose.test.yml build --no-cache
docker-compose -f docker-compose.test.yml up -d

# Production
docker-compose build --no-cache
docker-compose up -d
```

**Keine Breaking Changes** - Alle bestehenden Features bleiben funktional.

---

## Contributors

- Initial development and sprint forecasting implementation

---

## Links

- **Repository**: https://github.com/foe05/FrontEnd-SQLServer
- **Issues**: https://github.com/foe05/FrontEnd-SQLServer/issues
- **Releases**: https://github.com/foe05/FrontEnd-SQLServer/releases

---

[1.0.0]: https://github.com/foe05/FrontEnd-SQLServer/releases/tag/v1.0.0
