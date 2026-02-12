# 💾 SQLite Budget-Management Setup

## Übersicht

Das Budget-Management verwendet eine **SQLite-Datenbank** statt SQL Server. Dies ermöglicht:

- ✅ **Keine Schreibrechte auf SQL Server nötig** (nur Lesezugriff für Zeiterfassungsdaten)
- ✅ **Automatisches Setup** beim ersten Start
- ✅ **Einfaches Backup** (SQLite-Datei kopieren)
- ✅ **Persistente Speicherung** in Docker-Volume
- ✅ **Unabhängig von SQL Server-Verfügbarkeit**

## 📊 Architektur

```
┌─────────────────────────────────────────┐
│         Streamlit Dashboard             │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐    ┌──────────────┐ │
│  │  SQL Server  │    │   SQLite     │ │
│  │  (read-only) │    │ (read-write) │ │
│  └──────────────┘    └──────────────┘ │
│         │                    │         │
│    Zeit-           Budget-             │
│    erfassung      Verwaltung           │
│    (ZV)           (BudgetHistory)      │
└─────────────────────────────────────────┘
```

## 🚀 Installation & Setup

### 1. **Automatische Initialisierung**

Die SQLite-Datenbank wird **automatisch** beim ersten Start der Anwendung erstellt:

```python
# In config/budget_database.py
def ensure_tables_exist(self):
    """Erstellt Tabellen automatisch, falls sie nicht existieren"""
    # BudgetHistory Tabelle
    # Indizes für Performance
    # ...
```

**Beim ersten Start:**
1. Verzeichnis `data/` wird erstellt
2. Datei `data/budget.db` wird angelegt
3. Tabelle `BudgetHistory` wird erstellt
4. Indizes werden angelegt

**Keine manuelle Aktion erforderlich!** ✅

### 2. **Docker-Setup mit persistentem Storage**

#### **docker-compose.yml anpassen:**

```yaml
version: '3.8'

services:
  streamlit-dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SQL_SERVER_HOST=${SQL_SERVER_HOST}
      - SQL_SERVER_DATABASE=${SQL_SERVER_DATABASE}
      - SQL_SERVER_USERNAME=${SQL_SERVER_USERNAME}
      - SQL_SERVER_PASSWORD=${SQL_SERVER_PASSWORD}
    volumes:
      # SQLite Budget-Datenbank persistent speichern
      - ./data:/app/data
      # Optional: Logs persistent speichern
      - ./logs:/app/logs
    restart: unless-stopped
```

**Wichtig:** Volume `./data:/app/data` sorgt dafür, dass die SQLite-Datei auf dem Host gespeichert wird und bei Container-Neustarts erhalten bleibt.

### 3. **Lokales Setup (ohne Docker)**

```bash
# Einfach die Anwendung starten
streamlit run app.py

# SQLite-DB wird automatisch erstellt in:
# data/budget.db
```

## 📍 Speicherorte

### **Lokal:**
```
FrontEnd-SQLServer/
├── data/
│   └── budget.db          # SQLite-Datenbank
├── logs/
│   └── app.log
└── app.py
```

### **Docker:**
```
Container: /app/data/budget.db
Host:      ./data/budget.db  (via Volume)
```

## 🔍 Datenbank-Struktur

### **Tabelle: BudgetHistory**

```sql
CREATE TABLE BudgetHistory (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    ProjectID TEXT NOT NULL,
    Activity TEXT NOT NULL,
    Hours REAL NOT NULL CHECK(Hours >= 0),
    ChangeType TEXT NOT NULL CHECK(
        ChangeType IN ('initial', 'extension', 'correction', 'reduction')
    ),
    ValidFrom DATE NOT NULL,
    Reason TEXT NOT NULL,
    Reference TEXT,
    CreatedBy TEXT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indizes für Performance
CREATE INDEX idx_budget_project_activity
    ON BudgetHistory(ProjectID, Activity, ValidFrom DESC);

CREATE INDEX idx_budget_validfrom
    ON BudgetHistory(ValidFrom);

CREATE INDEX idx_budget_createdat
    ON BudgetHistory(CreatedAt DESC);
```

## 🎯 Verwendung

### **Im Dashboard:**

1. **Tab "💰 Budget-Verwaltung"** öffnen
2. Budgets erfassen und verwalten
3. Alles wird automatisch in SQLite gespeichert

### **API-Verwendung:**

```python
from config.budget_database import budget_db

# Budget speichern
budget_db.save_budget_entry(
    project_id='P24ABC01',
    activity='Implementierung',
    hours=100.0,
    change_type='initial',
    valid_from='2024-01-01',
    reason='Initialisierung',
    reference='V-2024-001',
    created_by='user@example.com'
)

# Budget abrufen (zu einem bestimmten Datum)
budgets = budget_db.get_all_budgets_at_date(
    projects=['P24ABC01'],
    target_date='2024-03-31'
)

# Historie anzeigen
history = budget_db.get_budget_history(
    project_id='P24ABC01',
    activity='Implementierung'
)
```

## 💾 Backup & Restore

### **Backup erstellen:**

```bash
# Lokal
cp data/budget.db data/budget_backup_$(date +%Y%m%d).db

# Docker
docker cp sql-server-dashboard:/app/data/budget.db ./backup/budget_$(date +%Y%m%d).db
```

### **Backup wiederherstellen:**

```bash
# Lokal
cp backup/budget_20240312.db data/budget.db

# Docker
docker cp ./backup/budget_20240312.db sql-server-dashboard:/app/data/budget.db
docker restart sql-server-dashboard
```

### **Automatisches Backup (Cron):**

```bash
# Backup täglich um 2 Uhr nachts
0 2 * * * cp /path/to/data/budget.db /path/to/backups/budget_$(date +\%Y\%m\%d).db
```

## 🔧 Administration

### **SQLite-Datenbank inspizieren:**

```bash
# SQLite CLI installieren
sudo apt-get install sqlite3  # Linux
brew install sqlite3          # macOS

# Datenbank öffnen
sqlite3 data/budget.db

# Befehle
.tables                 # Alle Tabellen anzeigen
.schema BudgetHistory   # Schema anzeigen
SELECT COUNT(*) FROM BudgetHistory;  # Anzahl Einträge
.quit                   # Beenden
```

### **Datenbank-Info im Dashboard:**

```python
from config.budget_database import budget_db

info = budget_db.get_database_info()
print(info)

# Output:
# {
#     'db_path': 'data/budget.db',
#     'db_size_bytes': 16384,
#     'db_size_mb': 0.02,
#     'table_count': 1,
#     'budget_entries': 15,
#     'unique_projects': 3,
#     'connection_ok': True
# }
```

### **Datenbank-Wartung:**

```sql
-- Vacuum (Speicherplatz optimieren)
VACUUM;

-- Integritätscheck
PRAGMA integrity_check;

-- Statistiken aktualisieren
ANALYZE;
```

## ⚠️ Wichtige Hinweise

### **Concurrent Access:**

SQLite unterstützt **mehrere Leser**, aber nur **einen Schreiber gleichzeitig**. Das ist für diese Anwendung ausreichend, da:
- Budget-Änderungen selten sind
- Meistens nur ein User gleichzeitig Budgets bearbeitet
- Lesezugriffe (Dashboard) sind unbegrenzt möglich

### **Skalierung:**

Für **sehr große Installationen** (>100 User parallel) könnte PostgreSQL oder MySQL besser geeignet sein. Für typische Projekt-Controlling-Szenarien ist SQLite perfekt ausreichend.

### **Berechtigungen:**

```bash
# Stellen Sie sicher, dass die Datei schreibbar ist
chmod 644 data/budget.db
chown <user>:<group> data/budget.db

# Docker: Container läuft als User 'streamlit'
# Volume-Permissions anpassen falls nötig
```

## 🐳 Docker-Compose Vollständiges Beispiel

```yaml
version: '3.8'

services:
  streamlit-dashboard:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: sql-server-dashboard
    ports:
      - "8501:8501"
    environment:
      # SQL Server (read-only für Zeiterfassung)
      - SQL_SERVER_HOST=sqlserver.example.com
      - SQL_SERVER_DATABASE=TimeTracking
      - SQL_SERVER_USERNAME=${SQL_SERVER_USERNAME}
      - SQL_SERVER_PASSWORD=${SQL_SERVER_PASSWORD}

      # Optional: Entra ID
      - ENTRA_CLIENT_ID=${ENTRA_CLIENT_ID}
      - ENTRA_CLIENT_SECRET=${ENTRA_CLIENT_SECRET}
      - ENTRA_TENANT_ID=${ENTRA_TENANT_ID}
    volumes:
      # SQLite Budget-DB persistent
      - ./data:/app/data
      # Logs persistent
      - ./logs:/app/logs
      # Cache persistent (optional)
      - ./cache:/app/cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  data:
  logs:
  cache:
```

## 🔄 Migration von SQL Server zu SQLite

Falls du bereits Budgets in SQL Server hattest (was bei dir nicht der Fall ist), hier der Migrationspfad:

```python
# Migration Script (nur als Referenz)
import sqlite3
import pyodbc

# SQL Server Daten lesen
sql_server_conn = pyodbc.connect(...)
cursor = sql_server_conn.cursor()
cursor.execute("SELECT * FROM BudgetHistory")
rows = cursor.fetchall()

# In SQLite schreiben
sqlite_conn = sqlite3.connect('data/budget.db')
sqlite_cursor = sqlite_conn.cursor()

for row in rows:
    sqlite_cursor.execute("""
        INSERT INTO BudgetHistory
        (ProjectID, Activity, Hours, ChangeType, ValidFrom, Reason, Reference, CreatedBy)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, row[1:])  # Skip ID

sqlite_conn.commit()
```

## ✅ Checkliste

- [ ] Volume `./data` in docker-compose.yml eingetragen
- [ ] Erste Budget-Einträge erfasst
- [ ] Backup-Strategie definiert
- [ ] Berechtigungen geprüft (`data/` Verzeichnis schreibbar)
- [ ] Test: Container neu starten → Daten bleiben erhalten

## 🆘 Troubleshooting

### Problem: "Database is locked"

**Ursache:** Mehrere Schreibzugriffe gleichzeitig

**Lösung:**
```python
# In budget_database.py ist bereits implementiert:
sqlite3.connect(self.db_path, check_same_thread=False)
```

### Problem: "Permission denied" beim Schreiben

**Lösung:**
```bash
# Verzeichnis schreibbar machen
chmod 755 data/
chmod 644 data/budget.db

# Docker: Volume-Permissions prüfen
```

### Problem: Datenbank verschwunden nach Container-Neustart

**Ursache:** Volume nicht korrekt gemountet

**Lösung:**
```yaml
# In docker-compose.yml:
volumes:
  - ./data:/app/data  # ← Absoluten oder relativen Pfad verwenden
```

---

**Bei Fragen: Issue erstellen oder Dokumentation konsultieren!** 🚀
