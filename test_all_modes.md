# 🧪 Alle Modi testen - Funktions-Parität sicherstellen

## 🚀 **Schneller Test aller Modi:**

### **1. SIMPLE Mode (Port 8503):**
```bash
docker build -f Dockerfile.simple -t dashboard-simple .
docker run -d -p 8503:8501 -e TEST_MODE=true --name test-simple dashboard-simple

# Test: http://localhost:8503
# Erwartung: Auto-Login, alle Features verfügbar
```

### **2. TEST Mode (Port 8502):**
```bash
docker-compose -f docker-compose.test.yml up -d

# Test: http://localhost:8502  
# Erwartung: Auto-Login, alle Features verfügbar
```

### **3. LOCAL Test Mode:**
```bash
cp .env.test .env
python -m streamlit run app.py

# Test: http://localhost:8501
# Erwartung: Auto-Login, alle Features verfügbar
```

## ✅ **Funktions-Checkliste (alle Modi müssen identisch sein):**

### **Login & Logout:**
- [ ] Auto-Login funktioniert
- [ ] Benutzer-Auswahl möglich
- [ ] Abmelden Button in Sidebar sichtbar
- [ ] Nach Abmeldung: Zurück zum Login
- [ ] Benutzer wechseln funktioniert

### **Dashboard Features:**
- [ ] Projekt-Zusammenfassung wird angezeigt
- [ ] Tätigkeits-Tabelle mit allen Spalten
- [ ] Sollstunden editierbar (Default: 0)
- [ ] Anteil am Projekt (%) wird berechnet
- [ ] Status-Ampeln (🟢🟡🔴) funktionieren

### **Filter & Interaktion:**
- [ ] Projekt-Auswahl (Multiselect)
- [ ] Jahr/Monat Filter
- [ ] Stunden-Quelle Auswahl (Zeit/FaktStd)
- [ ] Suche funktioniert
- [ ] Live-Update bei Änderungen

### **Export & Admin:**
- [ ] Excel Export verfügbar
- [ ] Health Check verfügbar (Admin-Benutzer)
- [ ] Cache-Management (Admin-Benutzer)

## 🔧 **Falls Probleme auftreten:**

### **Problem: Streamlit API Exception**
```bash
# Container Logs prüfen
docker logs <container-name>

# Streamlit Version prüfen
docker exec <container-name> python -c "import streamlit; print(streamlit.__version__)"
```

### **Problem: Abmelden funktioniert nicht**
```bash
# Session State Debug im Container
docker exec -it <container-name> python -c "
import streamlit as st
print('Session State Keys:', list(st.session_state.keys()) if hasattr(st, 'session_state') else 'Not available')
"
```

### **Problem: Keine Daten**
```bash
# Test-Daten prüfen
docker exec <container-name> ls -la /app/test_data/
docker exec <container-name> cat /app/test_data/zv_dummy_data.json | head -20
```

## 🎯 **Debug-Commands für alle Modi:**

### **Container Status:**
```bash
# Alle laufenden Container
docker ps

# Logs aller Modi
docker logs sql-server-dashboard-simple   # Simple
docker logs sql-server-dashboard-test     # Test  
docker logs sql-server-dashboard          # Production
```

### **Environment Check:**
```bash
# TEST_MODE Status in allen Containern
docker exec sql-server-dashboard-simple env | grep TEST_MODE
docker exec sql-server-dashboard-test env | grep TEST_MODE
docker exec sql-server-dashboard env | grep TEST_MODE || echo "Not set (correct for production)"
```

### **Interaktiver Debug:**
```bash
# Container betreten für Debug
docker exec -it sql-server-dashboard-simple bash
docker exec -it sql-server-dashboard-test bash

# Im Container:
# python -c "import os; print('TEST_MODE:', os.getenv('TEST_MODE'))"
# ls -la test_data/
# python -m streamlit --version
```

## 📋 **Expected Results:**

**Alle drei Modi sollten identische UI zeigen:**

1. **Login**: Auto-Login mit Test-Benutzern
2. **Sidebar**: Benutzer-Info + Abmelden Button
3. **Dashboard**: Projekt-Summary + Tätigkeits-Tabelle
4. **Features**: Stunden-Auswahl, Filter, Export
5. **Abmeldung**: Funktioniert, kehrt zum Login zurück

**Unterschiede nur bei:**
- **Port**: 8501/8502/8503
- **Build-Zeit**: 2min/5min/8min
- **Dependencies**: Minimal/Medium/Full
