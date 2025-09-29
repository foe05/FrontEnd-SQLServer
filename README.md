# SQL Server Dashboard - Zeiterfassung

Ein Streamlit-basiertes Dashboard für die Analyse von SQL Server Zeiterfassungsdaten mit Entra ID Authentifizierung.

## 🚀 Features

- **Benutzerauthentifizierung**: Microsoft Entra ID mit lokaler Entwicklungs-Fallback
- **Projektfilter**: Benutzer-spezifische Projektzugriffe
- **Editierbare Sollstunden**: Bearbeitbare Zielwerte pro Tätigkeit
- **Status-Ampel**: Visueller Erfüllungsstand (🟢 🟡 🔴)
- **Excel Export**: Formatierte Datenexporte
- **Docker Support**: Container-ready Deployment
- **Health Monitoring**: System-Health-Check Dashboard

## 📊 Dashboard Ansicht

| Tätigkeit/Activity | Sollstunden (verkauft) | Erfüllungsstand (%) | Status | Iststunden |
|--------------------|------------------------|-------------------|--------|-------------|
| Deployment | [Editable: 80] | 25% | 🟢 Buchbar | 20 STD |
| Design/Requirements | [Editable: 80] | 125% | 🔴 Überbucht | 100 STD |

## 🛠️ Installation

### Voraussetzungen

- Python 3.11+
- SQL Server mit ODBC Driver 17
- Docker (optional)

### 🧪 Schnellstart (TEST-MODUS - Empfohlen für Demo)

1. **Repository klonen**
```bash
git clone <repository-url>
cd FrontEnd-SQLServer
```

2. **Test-Umgebung starten**
```bash
# Option A: Mit Docker
docker-compose -f docker-compose.test.yml up -d

# Option B: Lokal
pip install -r requirements.txt
cp .env.test .env
streamlit run app.py
```

3. **Dashboard öffnen**
```
http://localhost:8502  # Docker
http://localhost:8501  # Lokal
```

4. **Sofort loslegen** 🚀
- ✅ Keine SQL Server Konfiguration nötig
- ✅ Keine Entra ID Setup erforderlich  
- ✅ Automatische Anmeldung mit Test-Benutzern
- ✅ Realistische Dummy-Daten bereits vorhanden

### Lokale Entwicklung (Vollständig)

1. **Repository klonen**
```bash
git clone <repository-url>
cd FrontEnd-SQLServer
```

2. **Python Environment einrichten**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Konfiguration**
```bash
cp .env.example .env
# .env Datei mit SQL Server Daten befüllen
```

4. **Anwendung starten**
```bash
streamlit run app.py
```

### Docker Deployment

1. **Docker Image bauen**
```bash
docker build -t streamlit-dashboard .
```

2. **Mit Docker Compose starten**
```bash
docker-compose up -d
```

3. **Dashboard öffnen**
```
http://localhost:8501
```

## ⚙️ Konfiguration

### Environment Variablen

**Produktion:**
```bash
# SQL Server
SQL_SERVER_HOST=your-server
SQL_SERVER_DATABASE=your-database
SQL_SERVER_USERNAME=user
SQL_SERVER_PASSWORD=password

# Entra ID (Optional)
ENTRA_CLIENT_ID=your-client-id
ENTRA_CLIENT_SECRET=your-secret
ENTRA_TENANT_ID=your-tenant-id
```

**TEST-MODUS (Schnellstart ohne Setup):**
```bash
# Aktiviert Test-Umgebung mit Dummy-Daten
TEST_MODE=true
# Alle anderen Variablen werden ignoriert
```

### Benutzer Konfiguration

`config/users.json`:
```json
{
  "users": {
    "user@company.com": {
      "projects": ["P24SAN06", "P24XYZ01"],
      "permissions": ["read", "export", "edit_targets"]
    }
  }
}
```

## 🗄️ Datenbankstruktur

Erwartet SQL Server Tabelle `ZV` mit folgenden Spalten:
- Name, Zeit, Projekt, Teilprojekt, Kostenstelle
- Verwendung, Status, Kommentar, Datum
- Jahr, Monat, Kundenname, etc.

**TEST-MODUS**: Verwendet Dummy-Daten, keine echte Datenbank erforderlich.

## 📈 Verwendung

### Authentifizierung

1. **Entra ID**: Automatische Weiterleitung zu Microsoft Login
2. **Lokal**: Entwicklungsumgebung mit Test-Benutzern

### Dashboard Navigation

1. **Projektauswahl**: Dropdown mit verfügbaren Projekten
2. **Filter**: Jahr/Monat/Quartal und Textsuche
3. **Tabelle**: Editierbare Sollstunden, automatischer Erfüllungsstand
4. **Export**: Excel-Download mit Formatierung

### Sollstunden bearbeiten

- Klicken Sie auf die Sollstunden-Spalte
- Neue Werte werden automatisch gespeichert
- Erfüllungsstand wird automatisch neu berechnet

## 🔍 Health Check

Zugriff über:
- UI: Admin Tools → Health Check
- API: `http://localhost:8501/health` (Docker)

Überprüft:
- Datenbankverbindung
- Authentifizierungsservice  
- Dateisystem-Zugriff
- Konfiguration

## 🐳 Docker Details

### Multi-Stage Build
- Optimierte Image-Größe
- Nur Runtime-Dependencies in Production

### Security Features
- Non-root User (streamlit)
- Minimal Base Image (python:3.11-slim)
- Resource Limits

### Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3
CMD curl -f http://localhost:8501/_stcore/health
```

## 🔧 Entwicklung

### Projektstruktur

```
streamlit-dashboard/
├── app.py                 # Hauptanwendung
├── config/
│   ├── users.json        # Benutzer & Berechtigungen
│   └── database.py       # DB Connection
├── components/
│   ├── auth.py           # Entra ID Authentication
│   ├── filters.py        # Filter Components
│   └── export.py         # Excel Export
├── utils/
│   ├── cache.py          # Caching System
│   └── health.py         # Health Monitoring
└── Dockerfile
```

### Tests ausführen

```bash
# Unit Tests (wenn implementiert)
python -m pytest tests/

# Manual Testing
streamlit run app.py
```

### Debug Modus

```bash
# Streamlit Debug
export STREAMLIT_SERVER_ENABLE_DEBUG=true
streamlit run app.py --server.address=0.0.0.0
```

## 📝 Logs & Monitoring

### Logs
- Container Logs: `docker logs sql-server-dashboard`
- File Logs: `logs/` Directory (wenn mounted)

### Metrics
- Streamlit Built-in Stats: `/_stcore/health`
- Custom Health Endpoint für Monitoring

## 🚨 Troubleshooting

### 🧪 TEST-MODUS Probleme

1. **Dashboard startet nicht**
```bash
# Stelle sicher dass TEST_MODE=true gesetzt ist
echo $TEST_MODE

# Prüfe ob Dummy-Daten existieren
ls -la test_data/

# Starte im Debug-Modus
TEST_MODE=true streamlit run app.py --server.headless false
```

2. **Keine Daten sichtbar**
```bash
# Test-Umgebung Container neu starten
docker-compose -f docker-compose.test.yml restart

# Oder lokale Dummy-Daten neu generieren
cd test_data && python dummy_data_generator.py
```

### Häufige Probleme (Produktivumgebung)

1. **SQL Server Connection**
```bash
# ODBC Driver prüfen
odbcinst -q -d

# Connection String testen
python -c "import pyodbc; print(pyodbc.drivers())"
```

2. **Entra ID Authentication**
```bash
# Redirect URI prüfen: http://localhost:8501
# Tenant ID und Client ID validieren
```

3. **Docker Health Check Failed**
```bash
# Container Status
docker ps
docker logs sql-server-dashboard

# Manual Health Check
docker exec sql-server-dashboard curl -f http://localhost:8501/_stcore/health
```

### 🔄 Zwischen Modi wechseln

```bash
# Zu TEST-MODUS wechseln
export TEST_MODE=true
streamlit run app.py

# Zu Produktivmodus wechseln
unset TEST_MODE
# oder
export TEST_MODE=false
streamlit run app.py
```

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/amazing-feature`)
3. Changes committen (`git commit -m 'Add amazing feature'`)
4. Branch pushen (`git push origin feature/amazing-feature`)
5. Pull Request erstellen

## 📄 License

Dieses Projekt ist unter der MIT License lizensiert - siehe die [LICENSE](LICENSE) Datei für Details.

## 🆘 Support

Bei Fragen oder Problemen:
1. Issues auf GitHub erstellen
2. Health Check Dashboard prüfen
3. Container Logs analysieren
4. Dokumentation konsultieren
