# 🔧 Installation & Debug Guide

## Problem 1: "streamlit command not found"

### Lösung A1 - Python direkt verwenden:
```powershell
# Statt "streamlit run app.py" verwenden Sie:
python -m streamlit run app.py
```

### Lösung A2 - Streamlit richtig installieren:
```powershell
# 1. Python Version prüfen
python --version

# 2. Pip aktualisieren
python -m pip install --upgrade pip

# 3. Streamlit installieren
python -m pip install streamlit

# 4. Installation prüfen
python -m streamlit --version

# 5. App starten
python -m streamlit run app.py
```

### Lösung A3 - Virtual Environment (Empfohlen):
```powershell
# 1. Virtual Environment erstellen
python -m venv venv

# 2. Aktivieren (Windows)
venv\Scripts\activate

# 3. Pakete installieren
pip install streamlit pandas openpyxl python-dotenv requests numpy

# 4. Test-Umgebung aktivieren
copy .env.test .env

# 5. App starten
streamlit run app.py
```

---

## Problem 2: Docker "Connection Refused"

### Debug-Schritte:

#### Schritt 1 - Container Status prüfen:
```powershell
# Laufende Container anzeigen
docker ps

# Alle Container (auch gestoppte)
docker ps -a

# Container Logs anzeigen (falls Container existiert)
docker logs sql-server-dashboard-simple
```

#### Schritt 2 - Build prüfen:
```powershell
# Manueller Build mit Debug-Output
docker build -f Dockerfile.simple -t test-dashboard . --no-cache

# Build erfolgreich? Dann starten:
docker run -d -p 8501:8501 -e TEST_MODE=true --name test-dash test-dashboard

# Container Logs in Echtzeit
docker logs -f test-dash
```

#### Schritt 3 - Port-Probleme:
```powershell
# Andere Port versuchen
docker run -d -p 8502:8501 -e TEST_MODE=true --name test-dash2 test-dashboard

# Browser: http://localhost:8502
```

#### Schritt 4 - Interactive Debug:
```powershell
# Container interaktiv starten
docker run -it -p 8501:8501 -e TEST_MODE=true test-dashboard bash

# Im Container:
# python -m streamlit run app.py
```

---

## Sofort-Lösung (Garantiert funktionierend):

### Windows PowerShell:
```powershell
# 1. Ins Projektverzeichnis
cd "C:\Users\johannesb\OneDrive - INTEND Geoinformatik GmbH\Dokumente\4 - Sideprojects DEV\GITHUB\FrontEnd-SQLServer\FrontEnd-SQLServer"

# 2. Python Module installieren
python -m pip install streamlit pandas openpyxl python-dotenv requests numpy plotly

# 3. Test-Umgebung
copy .env.test .env

# 4. App starten
python -m streamlit run app.py

# 5. Browser öffnen
start http://localhost:8501
```

### Alternative - Batch Script:
```batch
@echo off
echo Installing required packages...
python -m pip install streamlit pandas openpyxl python-dotenv requests numpy plotly

echo Setting up test environment...
copy .env.test .env

echo Starting dashboard...
python -m streamlit run app.py

pause
```

---

## Erwartete Ausgabe bei erfolgreichem Start:

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

---

## Falls alles fehlschlägt - Minimal Python Script:

```python
# test_install.py
import sys
print("Python version:", sys.version)

try:
    import streamlit
    print("✅ Streamlit available:", streamlit.__version__)
except ImportError:
    print("❌ Streamlit not installed")
    print("Install with: python -m pip install streamlit")

try:
    import pandas
    print("✅ Pandas available:", pandas.__version__)
except ImportError:
    print("❌ Pandas not installed")
```

Führen Sie aus: `python test_install.py`
