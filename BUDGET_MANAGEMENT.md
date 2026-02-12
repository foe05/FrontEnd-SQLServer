# 💰 Budget-Management System

## Übersicht

Das Budget-Management-System ermöglicht die **zeitbasierte Verwaltung von Projekt-Sollstunden** mit vollständiger Historie und Audit-Trail. Dies löst das Problem, dass Projektbudgets sich über die Laufzeit ändern können (Vertragsverlängerungen, Budgeterweiterungen, Korrekturen).

## 🎯 Hauptfunktionen

### 1. Zeitbasierte Budget-Gültigkeit
- Jede Budgetänderung hat ein **"Gültig ab"-Datum**
- Das Dashboard zeigt automatisch das **zum Filterdatum gültige Budget** an
- Ermöglicht historische Analysen: "Wie war der Projektstand im Januar?"

### 2. Vollständige Historie
- Alle Budgetänderungen werden mit **vollständigem Audit-Trail** gespeichert
- Begründung und Referenz (Vertragsnummer, Change Request) sind Pflichtfelder
- Änderungshistorie ist jederzeit einsehbar und exportierbar

### 3. Flexible Änderungstypen
- **🆕 Initial Budget**: Erstbudget bei Projektstart
- **📈 Extension**: Budgeterweiterung (z.B. Vertragsverlängerung)
- **🔧 Correction**: Korrektur (z.B. Fehler bei Erfassung)
- **📉 Reduction**: Budgetreduzierung (z.B. Leistungsänderung)

## 📊 Datenbank-Schema

### Tabelle: `BudgetHistory`

```sql
CREATE TABLE dbo.BudgetHistory (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID NVARCHAR(50) NOT NULL,           -- z.B. "P24ABC01"
    Activity NVARCHAR(200) NOT NULL,           -- z.B. "Implementierung"
    Hours DECIMAL(10,2) NOT NULL,              -- Stunden für diese Änderung
    ChangeType NVARCHAR(50) NOT NULL,          -- 'initial', 'extension', 'correction', 'reduction'
    ValidFrom DATE NOT NULL,                   -- Ab wann gilt diese Änderung
    Reason NVARCHAR(500) NOT NULL,             -- Begründung (Pflichtfeld)
    Reference NVARCHAR(200) NULL,              -- Vertragsnummer, Change Request, etc.
    CreatedBy NVARCHAR(200) NOT NULL,          -- User Email
    CreatedAt DATETIME2 DEFAULT GETDATE(),     -- Zeitstempel der Erfassung

    CONSTRAINT CK_BudgetHistory_Hours CHECK (Hours >= 0),
    CONSTRAINT CK_BudgetHistory_ChangeType CHECK (
        ChangeType IN ('initial', 'extension', 'correction', 'reduction')
    )
);
```

**Wichtige Indizes:**
- `IX_BudgetHistory_Project_Activity` auf (ProjectID, Activity, ValidFrom DESC)
- `IX_BudgetHistory_ValidFrom` auf (ValidFrom)
- `IX_BudgetHistory_CreatedAt` auf (CreatedAt DESC)

## 🚀 Installation & Setup

### 1. Datenbank-Tabelle erstellen

Führen Sie das SQL-Script aus:

```bash
# Mit sqlcmd (Windows)
sqlcmd -S <server> -d <database> -i sql/create_budget_history_table.sql

# Oder mit Azure Data Studio / SQL Server Management Studio
# Öffnen Sie die Datei sql/create_budget_history_table.sql und führen Sie sie aus
```

### 2. Anwendung neu starten

Nach der Tabellenerstellung starten Sie die Streamlit-Anwendung neu:

```bash
streamlit run app.py
```

## 📖 Verwendung

### Budget-Übersicht

**Tab: "💰 Budget-Verwaltung" → "📊 Budget-Übersicht"**

- Zeigt alle aktuellen Budgets für Ihre Projekte an
- **Stichtag-Auswahl**: Wählen Sie ein Datum, um das Budget zu diesem Zeitpunkt anzuzeigen
- Gruppiert nach Projekten mit Gesamtsummen
- Zeigt Anteil jeder Tätigkeit am Gesamtprojekt

**Beispiel:**
```
Stichtag: 15.06.2024
→ Zeigt alle Budgets, die bis zum 15.06.2024 erfasst wurden
→ Budgetänderungen vom 16.06.2024 oder später werden nicht berücksichtigt
```

### Budget erfassen/anpassen

**Tab: "💰 Budget-Verwaltung" → "➕ Budget erfassen/anpassen"**

1. **Projekt auswählen**: Wählen Sie das Projekt aus
2. **Tätigkeit eingeben**: Geben Sie die Tätigkeitsbezeichnung ein (z.B. "Implementierung")
3. **Stunden**: Anzahl der Stunden für diese Budgetänderung
4. **Änderungstyp**: Wählen Sie den passenden Typ
5. **Gültig ab**: Ab welchem Datum gilt diese Änderung (wichtig!)
6. **Referenz** (optional): Vertragsnummer, Change Request, etc.
7. **Begründung** (Pflicht): Erklären Sie die Budgetänderung

**Vorschau:** Das Formular zeigt automatisch eine Vorschau:
- Aktuelles Budget
- Änderung
- Neues Budget (= Aktuell + Änderung)

**Speichern:** Klicken Sie auf "💾 Budget speichern"

### Budget-Historie anzeigen

**Tab: "💰 Budget-Verwaltung" → "📜 Änderungshistorie"**

- Zeigt alle Budgetänderungen für ausgewählte Projekte
- **Filter**: Nach Projekt, Tätigkeit, Änderungstyp
- **Export**: Historie als CSV exportieren
- Vollständige Audit-Informationen (Wer, Wann, Warum, Referenz)

## 🔄 Zeitbasierte Budget-Berechnung

### Funktionsweise

**Budget zu einem Stichtag = Summe aller Einträge mit ValidFrom <= Stichtag**

**Beispiel:**

```
Projekt: P24ABC01
Tätigkeit: Implementierung

Budget-Historie:
1. 01.01.2024: 100h (initial)
2. 15.03.2024: +50h (extension - Vertragsverlängerung)
3. 01.06.2024: -20h (correction - Korrektur)

Budget-Berechnung:
- Stichtag 31.01.2024: 100h (nur Eintrag 1)
- Stichtag 31.03.2024: 150h (Einträge 1 + 2)
- Stichtag 30.06.2024: 130h (Einträge 1 + 2 + 3)
```

### Integration ins Dashboard

Das Dashboard berücksichtigt **automatisch den gefilterten Datumsbereich**:

1. **Datumsfilter setzen**: z.B. "01.01.2024 - 31.03.2024"
2. Dashboard zeigt:
   - **Ist-Stunden**: Nur für diesen Zeitraum
   - **Soll-Stunden**: Budget gültig am **31.03.2024** (Enddatum des Filters)

**Info-Box im Dashboard:**
```
💡 Budget-Berechnung: Die angezeigten Sollstunden gelten für den Stichtag 31.03.2024.
Budgetänderungen, die nach diesem Datum erfasst wurden, werden nicht berücksichtigt.
```

## 📋 Best Practices

### 1. Initial Budget erfassen

Beim Projektstart:
```
Typ: Initial Budget
Gültig ab: Projektstart-Datum
Referenz: Vertrags-Nummer
Begründung: "Initiales Projektbudget gemäß Vertrag XYZ-2024-001"
```

### 2. Vertragsverlängerung

Bei Vertragsverlängerung:
```
Typ: Extension
Gültig ab: Datum der Vertragsverlängerung
Referenz: Änderungsauftrag-Nummer
Begründung: "Vertragsverlängerung Q3/Q4 2024, zusätzliche 50h für Feature XYZ"
```

### 3. Budgetkorrektur

Bei Erfassungsfehler:
```
Typ: Correction
Gültig ab: Datum der Entdeckung oder ursprüngliches Datum
Referenz: Ticket-Nummer
Begründung: "Korrektur: Ursprünglich 120h statt 100h vereinbart"
```

### 4. Budgetreduzierung

Bei Leistungsreduzierung:
```
Typ: Reduction
Gültig ab: Datum der Änderung
Referenz: Change Request
Begründung: "Feature ABC entfernt aus Scope, Budget um 30h reduziert"
```

## 🔐 Berechtigungen

- **Budget erfassen**: Alle Benutzer können Budgets erfassen (keine Admin-Berechtigung nötig)
- **Historie einsehen**: Alle Benutzer können die Historie einsehen
- **Export**: Benutzer mit `export` Berechtigung können Historie exportieren

## 🧪 Test-Modus

Im Test-Modus (`TEST_MODE=true`):
- Budget-Daten werden **In-Memory** gespeichert
- Einige Test-Budgets werden automatisch erstellt
- Keine echte SQL-Datenbank erforderlich
- Ideal für Entwicklung und Demo

**Initialisierte Test-Budgets:**
- P24ABC01 / Implementierung: 100h
- P24ABC01 / Testing & QA: 50h
- P24XYZ01 / Implementierung: 80h

## 🔍 Troubleshooting

### Problem: "Tabelle 'BudgetHistory' existiert nicht"

**Lösung:** Führen Sie das SQL-Script aus:
```bash
sqlcmd -S <server> -d <database> -i sql/create_budget_history_table.sql
```

### Problem: "Budget-Änderungen werden nicht angezeigt"

**Prüfen:**
1. Ist das "Gültig ab"-Datum <= Stichtag im Dashboard?
2. Wurde die Änderung erfolgreich gespeichert? (Erfolgsmeldung prüfen)
3. Cache leeren: Sidebar → Admin Tools → "🧹 Cache leeren"

### Problem: "Budgets stimmen nicht mit alter Version überein"

**Erklärung:** Das neue System verwendet die **SQL-Datenbank** statt Dateisystem.

**Migration:**
1. Alte Budgets müssen neu erfasst werden
2. Oder: Migrationsscript erstellen (siehe unten)

## 📤 Migration von altem System

Wenn Sie bestehende Budgets aus dem alten Dateisystem-basierten System migrieren möchten:

### Option 1: Manuelle Erfassung (Empfohlen)

1. Öffnen Sie `cache/targets_*.json` Dateien
2. Erfassen Sie jeden Eintrag manuell im neuen System
3. Verwenden Sie Typ "Initial Budget"
4. Setzen Sie "Gültig ab" auf das Projektstart-Datum

### Option 2: Automatische Migration (Fortgeschritten)

```python
import json
import os
from datetime import date
from config.database import db_config

# Lesen Sie alte Cache-Dateien
cache_dir = "cache"
for filename in os.listdir(cache_dir):
    if filename.startswith('targets_') and filename.endswith('.json'):
        filepath = os.path.join(cache_dir, filename)

        with open(filepath, 'r') as f:
            data = json.load(f)

        # Extrahieren Sie Projekt und Activity
        project = data.get('project')
        activity = data.get('activity')
        hours = data.get('target_hours', 0)

        # Speichern Sie in neue Datenbank
        db_config.save_budget_entry(
            project_id=project,
            activity=activity,
            hours=hours,
            change_type='initial',
            valid_from='2024-01-01',  # Anpassen!
            reason='Migration von altem System',
            reference='MIGRATION-2024',
            created_by='admin@company.com'
        )

        print(f"Migriert: {project} - {activity} - {hours}h")
```

## 🔗 API-Referenz

### Datenbankfunktionen

#### `db_config.save_budget_entry()`
```python
success = db_config.save_budget_entry(
    project_id='P24ABC01',
    activity='Implementierung',
    hours=100.0,
    change_type='initial',
    valid_from='2024-01-01',
    reason='Initialisierung',
    reference='V-2024-001',
    created_by='user@example.com'
)
```

#### `db_config.get_budget_at_date()`
```python
budget = db_config.get_budget_at_date(
    project_id='P24ABC01',
    activity='Implementierung',
    target_date='2024-03-31'
)
# Returns: 100.0 (Summe aller Einträge bis 31.03.2024)
```

#### `db_config.get_all_budgets_at_date()`
```python
budgets = db_config.get_all_budgets_at_date(
    projects=['P24ABC01', 'P24XYZ01'],
    target_date='2024-03-31'
)
# Returns: {'P24ABC01': {'Implementierung': 100.0, 'Testing': 50.0}, ...}
```

#### `db_config.get_budget_history()`
```python
history = db_config.get_budget_history(
    project_id='P24ABC01',
    activity='Implementierung'  # Optional
)
# Returns: DataFrame with all budget entries
```

## 📚 Weitere Ressourcen

- **SQL-Script**: [sql/create_budget_history_table.sql](sql/create_budget_history_table.sql)
- **Komponente**: [components/budget_manager.py](components/budget_manager.py)
- **Datenbank-Funktionen**: [config/database.py](config/database.py)
- **Test-Modus**: [config/test_database.py](config/test_database.py)

## 💡 Tipps

1. **Gültig ab-Datum sorgfältig wählen**: Dieses Datum bestimmt, ab wann das Budget gilt
2. **Begründungen dokumentieren**: Hilft bei späteren Audits und Nachvollziehbarkeit
3. **Referenzen verwenden**: Verknüpfen Sie Budgetänderungen mit Verträgen/Change Requests
4. **Regelmäßige Exports**: Exportieren Sie die Historie regelmäßig als Backup

## 🎉 Vorteile des neuen Systems

✅ **Zeitbasierte Analysen**: "Wie stand das Projekt im Q1?"
✅ **Vollständige Historie**: Jede Änderung ist dokumentiert
✅ **Audit-Trail**: Wer hat wann was geändert und warum?
✅ **Flexibilität**: Budgets können sich über die Zeit ändern
✅ **Korrektheit**: Historische Auswertungen zeigen das damals gültige Budget
✅ **Compliance**: Erfüllt Anforderungen an Controlling und Nachweisbarkeit

---

**Fragen oder Probleme?**
Erstellen Sie ein Issue im Repository oder kontaktieren Sie den Administrator.
