# 🚀 SCHNELLSTART - Sofort loslegen!

## Option 1: 💻 LOKAL (Empfohlen - Keine Docker-Probleme)

```bash
# 1. Python Pakete installieren (ohne pyodbc)
pip install streamlit pandas msal openpyxl python-dotenv requests numpy plotly

# 2. Test-Umgebung aktivieren
cp .env.test .env

# 3. Dashboard starten
streamlit run app.py
```

**➡️ Fertig!** Dashboard läuft auf: http://localhost:8501

---

## Option 2: 🐳 Docker (Falls Sie Docker bevorzugen)

```bash
# Fix wurde angewendet - sollte jetzt funktionieren:
docker build -f Dockerfile.simple -t test-dashboard .
docker run -p 8501:8501 -e TEST_MODE=true test-dashboard
```

**➡️ Dashboard läuft auf:** http://localhost:8501

---

## ✨ Was Sie erwarten können:

### 🧪 TEST-MODUS Features:
- ✅ **Automatischer Login** - Keine Authentifizierung nötig
- ✅ **Realistische Dummy-Daten** - 3 Projekte mit Zeitdaten
- ✅ **Editierbare Sollstunden** - Testen Sie die Hauptfunktion
- ✅ **Excel Export** - Funktioniert mit Test-Daten
- ✅ **Alle Filter** - Jahr, Monat, Projekte, Suche

### 📊 Test-Daten:
- **Projekte**: P24ABC01, P24XYZ01, P24DEF02
- **Tätigkeiten**: Analyse, Design, Implementierung, Testing, Deployment
- **Zeitraum**: Januar-Februar 2024
- **Benutzer**: test@company.com, demo@company.com, viewer@company.com

---

## 🔧 Problemlösung:

### Falls Fehler auftreten:

**ImportError: pyodbc**
```bash
# Installieren Sie nur die nötigen Pakete:
pip install streamlit pandas openpyxl python-dotenv requests
```

**Permission Denied (Docker)**
```bash
# Verwenden Sie lokale Option:
streamlit run app.py
```

**Port bereits belegt**
```bash
# Anderen Port verwenden:
streamlit run app.py --server.port 8502
```

---

## 🎯 Nächste Schritte:

1. **Dashboard testen** ✅
2. **Sollstunden editieren** - Klicken Sie in die Sollstunden-Spalte
3. **Filter ausprobieren** - Jahr/Monat/Projekt ändern
4. **Excel Export** - Button "Zusammenfassung exportieren"
5. **Verschiedene Benutzer** - Logout → anderen Test-Benutzer wählen

---

## 📋 Vergleich der Optionen:

| Methode | Setup-Zeit | Probleme | Geschwindigkeit |
|---------|------------|----------|-----------------|
| **Lokal** | 30 Sekunden | Keine | Sehr schnell ⚡ |
| **Docker Simple** | 2-5 Minuten | Minimal | Schnell 🚀 |
| **Docker Full** | 5-10 Minuten | Möglich | Mittel 🐳 |

**Empfehlung**: Starten Sie mit der lokalen Option! 💻✨
