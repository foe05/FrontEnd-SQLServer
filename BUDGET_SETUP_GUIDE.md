# 🚀 Budget-Management System - Quick Setup Guide

## Schritt-für-Schritt Anleitung

### 1. SQL-Tabelle erstellen

**Option A: Mit sqlcmd (Command Line)**

```bash
# Windows
sqlcmd -S <ServerName> -d <DatabaseName> -i sql\create_budget_history_table.sql

# Windows mit Integrated Authentication
sqlcmd -S localhost -d TimeTracking -E -i sql\create_budget_history_table.sql

# Windows mit Username/Password
sqlcmd -S localhost -d TimeTracking -U <username> -P <password> -i sql\create_budget_history_table.sql
```

**Option B: Mit Azure Data Studio / SQL Server Management Studio**

1. Öffnen Sie Azure Data Studio oder SSMS
2. Verbinden Sie sich mit Ihrem SQL Server
3. Öffnen Sie die Datei `sql/create_budget_history_table.sql`
4. Führen Sie das Script aus (F5)
5. Prüfen Sie die Ausgabe auf Fehler

**Option C: Mit Python Script**

```python
import pyodbc
from config.database import db_config

# Lesen Sie das SQL-Script
with open('sql/create_budget_history_table.sql', 'r') as f:
    sql_script = f.read()

# Führen Sie es aus
try:
    with pyodbc.connect(db_config.connection_string) as conn:
        cursor = conn.cursor()
        # Split by GO and execute each batch
        for batch in sql_script.split('GO'):
            if batch.strip():
                cursor.execute(batch)
        conn.commit()
    print("✅ Tabelle erfolgreich erstellt!")
except Exception as e:
    print(f"❌ Fehler: {e}")
```

### 2. Anwendung neu starten

```bash
# Stoppen Sie die laufende Anwendung (Ctrl+C)

# Starten Sie neu
streamlit run app.py

# Oder mit Docker
docker-compose restart
```

### 3. Budget-Management-Tab öffnen

1. Melden Sie sich im Dashboard an
2. Navigieren Sie zum Tab **"💰 Budget-Verwaltung"**
3. Sie sollten drei Sub-Tabs sehen:
   - 📊 Budget-Übersicht
   - ➕ Budget erfassen/anpassen
   - 📜 Änderungshistorie

### 4. Erstes Budget erfassen

**Beispiel: Initial Budget für ein Projekt**

1. Gehen Sie zu **"➕ Budget erfassen/anpassen"**
2. Füllen Sie das Formular aus:
   - **Projekt**: P24ABC01 (oder Ihr Projektname)
   - **Tätigkeit**: Implementierung
   - **Stunden**: 100
   - **Änderungstyp**: 🆕 Initial Budget
   - **Gültig ab**: Projektstart-Datum (z.B. 01.01.2024)
   - **Referenz**: Vertrag-2024-001
   - **Begründung**: Initialisiertes Projektbudget gemäß Kundenvertrag
3. Klicken Sie auf **"💾 Budget speichern"**
4. Sie sollten eine Erfolgsmeldung sehen

### 5. Budget im Dashboard prüfen

1. Gehen Sie zum Tab **"📊 Übersicht"**
2. Sie sollten eine Info-Box sehen:
   ```
   💡 Budget-Berechnung: Die angezeigten Sollstunden gelten für den Stichtag XX.XX.XXXX
   ```
3. Die Sollstunden in der Tabelle sollten nun Ihre erfassten Budgets anzeigen

## 🧪 Test-Modus (ohne SQL Server)

Wenn Sie das System zunächst ohne echten SQL Server testen möchten:

1. Setzen Sie die Umgebungsvariable:
   ```bash
   export TEST_MODE=true
   # Windows: set TEST_MODE=true
   ```

2. Starten Sie die Anwendung:
   ```bash
   streamlit run app.py
   ```

3. Das System lädt automatisch Test-Budgets:
   - P24ABC01 / Implementierung: 100h
   - P24ABC01 / Testing & QA: 50h
   - P24XYZ01 / Implementierung: 80h

## 🔍 Überprüfung der Installation

### Prüfen Sie, ob die Tabelle existiert:

```sql
SELECT COUNT(*) as TableExists
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME = 'BudgetHistory';
-- Sollte 1 zurückgeben
```

### Prüfen Sie die Tabellenstruktur:

```sql
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'BudgetHistory'
ORDER BY ORDINAL_POSITION;
```

### Prüfen Sie die Indizes:

```sql
SELECT name, type_desc
FROM sys.indexes
WHERE object_id = OBJECT_ID('dbo.BudgetHistory');
```

### Erstellen Sie einen Test-Eintrag:

```sql
INSERT INTO BudgetHistory (
    ProjectID, Activity, Hours, ChangeType, ValidFrom,
    Reason, Reference, CreatedBy
) VALUES (
    'P24TEST01',
    'Test-Tätigkeit',
    50.0,
    'initial',
    '2024-01-01',
    'Test-Eintrag zur Verifizierung',
    'TEST-001',
    'test@example.com'
);

-- Prüfen
SELECT * FROM BudgetHistory WHERE ProjectID = 'P24TEST01';
```

## ❌ Häufige Fehler und Lösungen

### Fehler: "Invalid object name 'BudgetHistory'"

**Ursache:** Tabelle wurde nicht erstellt

**Lösung:**
1. Prüfen Sie, ob Sie mit der richtigen Datenbank verbunden sind
2. Führen Sie das SQL-Script erneut aus
3. Prüfen Sie die Ausgabe auf Fehlermeldungen

### Fehler: "Cannot insert NULL into column 'Reason'"

**Ursache:** Begründung wurde nicht ausgefüllt

**Lösung:**
- Stellen Sie sicher, dass das Feld "Begründung" ausgefüllt ist
- Dies ist ein Pflichtfeld

### Fehler: "The INSERT statement conflicted with the CHECK constraint"

**Ursache:** Ungültiger Wert für `ChangeType` oder negative Stunden

**Lösung:**
- `ChangeType` muss einer der folgenden sein: 'initial', 'extension', 'correction', 'reduction'
- `Hours` muss >= 0 sein

### Fehler: "Database connection failed"

**Ursache:** SQL Server nicht erreichbar

**Lösung:**
1. Prüfen Sie die `.env` Datei:
   ```
   SQL_SERVER_HOST=localhost
   SQL_SERVER_DATABASE=TimeTracking
   SQL_SERVER_USERNAME=...
   SQL_SERVER_PASSWORD=...
   ```
2. Testen Sie die Verbindung:
   ```python
   from config.database import db_config
   print(db_config.test_connection())  # Sollte True sein
   ```

## 📝 Nächste Schritte

Nach erfolgreicher Installation:

1. **Budgets für alle Projekte erfassen**
   - Verwenden Sie Typ "Initial Budget"
   - Setzen Sie "Gültig ab" auf Projektstart

2. **Dokumentation lesen**
   - Siehe [BUDGET_MANAGEMENT.md](BUDGET_MANAGEMENT.md) für Details

3. **Best Practices anwenden**
   - Immer Begründungen dokumentieren
   - Referenzen zu Verträgen/Change Requests angeben
   - Sorgfältiges Setzen des "Gültig ab"-Datums

4. **Team schulen**
   - Erklären Sie dem Team das neue System
   - Demonstrieren Sie die zeitbasierte Funktionsweise

## 🆘 Support

Bei Problemen:
1. Prüfen Sie die Logs: `logs/` Verzeichnis
2. Aktivieren Sie Debug-Modus: `export STREAMLIT_SERVER_ENABLE_DEBUG=true`
3. Konsultieren Sie [BUDGET_MANAGEMENT.md](BUDGET_MANAGEMENT.md)
4. Erstellen Sie ein Issue im Repository

## ✅ Checkliste

- [ ] SQL-Tabelle `BudgetHistory` erstellt
- [ ] Tabelle mit Test-Eintrag verifiziert
- [ ] Anwendung neu gestartet
- [ ] Budget-Management-Tab ist sichtbar
- [ ] Erstes Budget erfolgreich erfasst
- [ ] Budget erscheint im Dashboard
- [ ] Info-Box zur Budget-Berechnung wird angezeigt
- [ ] Historie ist einsehbar
- [ ] Team ist geschult

---

**Viel Erfolg mit dem neuen Budget-Management-System! 🎉**
