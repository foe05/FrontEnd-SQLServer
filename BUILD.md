# Docker Build Anleitung

## Problem mit Microsoft ODBC Driver

Das ursprüngliche Problem war, dass `apt-key` in neueren Debian-Versionen deprecated ist. Das wurde im aktuellen `Dockerfile` behoben.

## Build-Optionen

### 1. 🧪 TEST-MODUS (Empfohlen für schnelle Demo)

**Vorteile:**
- ✅ Keine SQL Server ODBC Driver Installation nötig
- ✅ Schneller Build (weniger Dependencies)
- ✅ Funktioniert immer, auch ohne Internet-Zugang zu Microsoft Repositories
- ✅ Ideal für Entwicklung und Demo

**Build und Run:**
```bash
# Build Test-Container (schnell, keine ODBC Dependencies)
docker-compose -f docker-compose.test.yml build

# Starten
docker-compose -f docker-compose.test.yml up -d

# Zugriff
http://localhost:8502
```

**Was passiert:**
- Verwendet `Dockerfile.test` (vereinfacht, ohne ODBC)
- Automatisch `TEST_MODE=true`
- Dummy-Daten aus `test_data/`
- Keine Authentifizierung erforderlich

### 2. 🏭 PRODUKTIV-MODUS (Mit SQL Server Support)

**Vorteile:**
- ✅ Vollständige SQL Server Integration
- ✅ Microsoft ODBC Driver 17 enthalten
- ✅ Entra ID Authentication Support
- ✅ Produktionsreif

**Build und Run:**
```bash
# Build Production-Container (mit ODBC, dauert länger)
docker build -t streamlit-dashboard .

# Oder mit docker-compose
docker-compose build

# Starten mit Umgebungsvariablen
docker-compose up -d
```

**Voraussetzungen:**
- SQL Server Zugang
- Environment Variables konfiguriert (`.env` Datei)
- Optional: Entra ID App Registration

## Troubleshooting

### Problem: Permission denied - cannot create directory '/home/streamlit'

**Ursache:** Docker Benutzer-Berechtigung Problem beim Erstellen von Home-Verzeichnissen.

**Lösung 1 - Ultra-einfache Version (Empfohlen):**
```bash
# Verwende simplified Dockerfile ohne Benutzer-Probleme
docker build -f Dockerfile.simple -t dashboard-simple .
docker run -p 8501:8501 -e TEST_MODE=true dashboard-simple
```

**Lösung 2 - Lokale Entwicklung (Keine Docker-Probleme):**
```bash
pip install -r requirements.txt
cp .env.test .env
streamlit run app.py
```

### Problem: Microsoft Repository nicht erreichbar

**Lösung 1 - Test-Modus verwenden:**
```bash
docker-compose -f docker-compose.test.yml up -d
```

**Lösung 2 - Build mit anderem Base Image:**
```dockerfile
# Alternative: Ubuntu 20.04 basis
FROM python:3.11-slim
# Oder explizit:
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y python3 python3-pip
```

### Problem: GPG Key Issues

**Diagnose:**
```bash
# Container debuggen
docker build --target builder -t debug-build .
docker run -it debug-build bash

# Manual key installation testen
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
```

### Problem: Network/Proxy Issues

**Lösung - Build Args für Proxy:**
```bash
docker build \
  --build-arg http_proxy=http://proxy:8080 \
  --build-arg https_proxy=http://proxy:8080 \
  -t streamlit-dashboard .
```

## Performance Vergleich

| Build Option | Build Zeit | Image Größe | Use Case |
|--------------|------------|-------------|----------|
| `Dockerfile.test` | ~2-3 min | ~800 MB | Demo, Entwicklung |
| `Dockerfile` | ~5-8 min | ~1.2 GB | Produktion |

## Empfohlener Workflow

### 1. Entwicklung/Demo starten:
```bash
# Schneller Start ohne Setup
docker-compose -f docker-compose.test.yml up -d
```

### 2. Für Produktion vorbereiten:
```bash
# .env konfigurieren
cp .env.example .env
# SQL Server Details eintragen

# Production Build
docker-compose up -d
```

### 3. Bei Build-Problemen:
```bash
# Test-Modus als Fallback
docker-compose -f docker-compose.test.yml up -d
```

## Manueller Build ohne docker-compose

### Test-Version:
```bash
docker build -f Dockerfile.test -t dashboard-test .
docker run -p 8501:8501 -e TEST_MODE=true dashboard-test
```

### Production-Version:
```bash
docker build -t dashboard-prod .
docker run -p 8501:8501 --env-file .env dashboard-prod
```
