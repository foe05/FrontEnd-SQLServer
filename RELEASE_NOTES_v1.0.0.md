# 🚀 Release Notes v1.0.0 - Initial Release

**Release Date**: 30. September 2025  
**Git Tag**: `v1.0.0`  
**Branch**: `main` (merged from `feature/zeitreihen`)

---

## 🎉 **Erste Production-Ready Version!**

Das SQL Server Dashboard ist jetzt vollständig einsatzbereit mit umfassenden Zeitreihen- und Prognose-Funktionen.

---

## 🌟 **Highlights**

### **Sprint-basierte Budget-Prognosen**
- **Gewichtete 4-Sprint-Analyse**: Neueste Sprints haben höheres Gewicht (40% → 30% → 20% → 10%)
- **3 Prognose-Szenarien**: Optimistisch/Realistisch/Pessimistisch mit Konfidenz-Levels
- **Automatische Berechnung**: Basierend auf historischer Sprint-Velocity
- **Manuelle Overrides**: Eigene Einschätzungen mit Begründung speichern

### **Interaktive Visualisierungen**
- **Burn-down Charts** mit 3 farbigen Szenario-Linien
- **Sprint-Velocity Analysis** mit Trend-Erkennung
- **Wochentrend-Charts** mit Durchschnitts-Linien
- **Activity-Vergleichs-Charts** über Zeit
- **Live-Updates** bei allen Wert-Änderungen

### **Flexible Deployment-Optionen**
- **SIMPLE Mode** (Port 8503): Schnellstart ohne Setup (~2 min Build)
- **TEST Mode** (Port 8502): Vollständig mit Security (~3 min Build)
- **PRODUCTION Mode** (Port 8501): SQL Server + Entra ID (~8 min Build)

---

## 📦 **Was ist neu in v1.0.0**

### **Zeitreihen & Prognosen**
```
✅ Sprint-basierte Forecasts (4 Sprints à 2 Wochen)
✅ Prognose-Szenarien (Best/Realistic/Worst Case)
✅ Budget-Ende-Datum mit Konfidenz-Bereichen
✅ Velocity-Trend-Erkennung (steigend/fallend/stabil)
✅ Manuelle Prognose-Overrides mit Persistierung
✅ Sprint-Velocity Charts für Performance-Analyse
✅ Wochentrend-Visualisierungen
✅ Activity-Level Forecasting
```

### **Dashboard-Funktionalität**
```
✅ Projekt-Zusammenfassung (Soll vs. Ist)
✅ Editierbare Sollstunden (Default: 0)
✅ Prozentuale Anteile am Gesamtprojekt
✅ Flexible Stunden-Quelle (Zeit vs. FaktStd)
✅ Status-Ampeln (🟢 🟡 🔴)
✅ Excel Export mit Formatierung
✅ Tab-Navigation (Übersicht | Zeitreihen | Export)
```

### **Authentication & Security**
```
✅ Microsoft Entra ID Integration
✅ Lokale Entwicklungs-Fallback
✅ TEST_MODE mit Auto-Login
✅ Benutzerverwaltung via JSON
✅ Session State Management
✅ Funktionierende Logout/Benutzer-Wechsel-Funktion
```

### **Docker & Deployment**
```
✅ 3 Deployment-Modi (Simple/Test/Production)
✅ Multi-Stage Docker Builds
✅ Non-root Container (Security)
✅ Health Check Endpoint
✅ iframe Embedding für Azure DevOps
✅ CORS Support aktiviert
```

---

## 🔧 **Technische Details**

### **Stack:**
- **Frontend**: Streamlit (Python 3.11+)
- **Database**: SQL Server (ZV Tabelle) via pyodbc
- **Auth**: Microsoft Entra ID (msal-python)
- **Visualization**: Plotly >= 5.18.0
- **Analytics**: scikit-learn >= 1.3.0
- **Container**: Docker python:3.11-slim

### **Neue Dependencies:**
```
plotly>=5.18.0 (updated von 5.17.0)
scikit-learn>=1.3.0 (neu)
```

### **Neue Dateien:**
```
components/
  ├─ burndown_chart.py (510 Zeilen)
  ├─ forecast_ui.py (413 Zeilen)
utils/
  └─ forecast_engine.py (265 Zeilen)
```

### **Code-Statistik:**
```
16 Dateien geändert
2.586 Zeilen hinzugefügt
56 Zeilen entfernt
8 neue Dokumentations-Dateien
```

---

## 🚀 **Installation & Start**

### **Schnellstart (TEST_MODE):**
```bash
# Lokale Installation
pip install -r requirements.test.txt
cp .env.test .env
python -m streamlit run app.py

# Docker (empfohlen)
docker-compose -f docker-compose.test.yml up -d
# → http://localhost:8502
```

### **Produktions-Deployment:**
```bash
# .env konfigurieren mit SQL Server Details
cp .env.example .env
# SQL_SERVER_HOST, DATABASE, etc. eintragen

# Docker Build & Start
docker-compose build
docker-compose up -d
# → http://localhost:8501
```

---

## 📊 **Usage Examples**

### **Budget-Prognose nutzen:**
```
1. Tab "Übersicht" → Sollstunden setzen (z.B. 200h)
2. Tab "Zeitreihen" → "Projekt-Übersicht" wählen
3. Prognose-Szenarien werden automatisch berechnet
4. Optional: "Manuelle Prognose" aktivieren für eigene Werte
5. Charts zeigen 3 Szenario-Linien (grün/orange/rot)
```

### **Manuelle Prognose speichern:**
```
1. Tab "Zeitreihen" → Checkbox "Manuelle Prognose aktivieren"
2. Wert eingeben: z.B. "60h/Sprint"
3. Begründung: "Team-Urlaub im Oktober"
4. "Speichern" klicken
→ Prognose wird persistiert und Charts aktualisieren
```

### **Velocity-Trend analysieren:**
```
1. Tab "Zeitreihen" → "Projekt-Übersicht"
2. Expandiere "Sprint-Velocity Analyse"
3. Balkendiagramm zeigt letzte 4 Sprints
4. Gewichteter Durchschnitt als Linie
5. Automatische Trend-Warnung wenn Velocity sinkt
```

---

## 🐛 **Known Issues**

Keine bekannten Fehler in v1.0.0.

---

## 🔮 **Future Roadmap (v1.1.0+)**

Mögliche zukünftige Features:
- Monte-Carlo-Simulation für robustere Prognosen
- Meilenstein-Marker in Charts
- Team-Kapazitäts-Planung (Urlaube berücksichtigen)
- Historische Forecast-Genauigkeit tracken
- Export von Charts als PNG/PDF
- Sprint-Retrospective Ansicht
- Multi-Language Support (EN/DE)

---

## 💬 **Feedback & Support**

- **Issues**: https://github.com/foe05/FrontEnd-SQLServer/issues
- **Pull Requests**: https://github.com/foe05/FrontEnd-SQLServer/pulls
- **Dokumentation**: Siehe README.md und *.md Dateien im Repository

---

## 🙏 **Acknowledgments**

Entwickelt mit:
- Streamlit Framework
- Plotly für Visualisierungen
- Microsoft SQL Server
- Docker für Container-Deployment

---

**Viel Erfolg mit dem SQL Server Dashboard v1.0.0! 🎉**

Für Fragen oder Probleme, bitte ein Issue auf GitHub erstellen.
