# 📈 Zeitreihen-Features - Anleitung

## 🎯 **Budget-Ende & Budget-Status Felder**

### **Was zeigen diese Felder?**

#### **Budget-Ende (Prognose):**
Prognostiziert, **wann Ihr Projektbudget erschöpft** sein wird, basierend auf:
- ✅ Durchschnittliche Buchungsrate der **letzten 4 Wochen**
- ✅ Verbleibende Sollstunden
- ✅ Linearer Trend in die Zukunft

**Beispiel:**
```
Sollstunden: 100h
Bereits gebucht: 60h
Verbleibend: 40h
Ø letzte 4 Wochen: 10h/Woche
→ Budget-Ende: in 4 Wochen (+ Datum)
```

#### **Budget-Status:**
Zeigt den aktuellen Status, wenn **keine Prognose** möglich ist:
- **"⚠️ Erschöpft"** - Budget bereits überschritten
- **"Keine Aktivität"** - Keine Buchungen in letzten 4 Wochen
- **"Keine Prognose"** - Sollstunden = 0 oder keine Daten

---

## ❓ **Warum zeigt es "Keine Prognose" / "Keine Aktivität"?**

### **Grund 1: Sollstunden = 0 (Standard)**
Sie haben die Sollstunden noch nicht gesetzt!

**Lösung:**
```
1. Gehen Sie zum Tab "📊 Übersicht"
2. Klicken Sie in die "Sollstunden" Spalte
3. Tragen Sie Ihre verkauften Stunden ein (z.B. 80, 120, etc.)
4. Wechseln Sie zurück zum Tab "📈 Zeitreihen"
→ Budget-Ende wird jetzt berechnet!
```

### **Grund 2: Keine Buchungen in letzten 4 Wochen**
Die Dummy-Daten sind alt (Jan-Sep 2024), aber wir sind jetzt in September 2025!

**Lösung A - Aktuellere Dummy-Daten:**
Die Dummy-Daten werden automatisch angepasst, wenn Sie:
```
- Projekt wechseln
- Dashboard neu laden
```

**Lösung B - Produktiv-Modus:**
Mit echten SQL Server Daten aus der ZV-Tabelle funktioniert die Prognose automatisch.

---

## 🧪 **So testen Sie die Features:**

### **Schritt-für-Schritt Anleitung:**

**1. Sollstunden setzen:**
```
Tab "📊 Übersicht" öffnen
→ Klick in Sollstunden-Spalte für "Implementierung"
→ Wert eingeben: 100
→ Enter drücken
```

**2. Zeitreihen-Tab öffnen:**
```
Tab "📈 Zeitreihen" klicken
→ "Projekt-Übersicht" wählen
→ Burn-down Chart erscheint
```

**3. Erwartete Anzeige (bei korrekten Daten):**
```
┌─────────────────────────────────────────────────┐
│ Sollstunden │ Ist-Stunden │ Erfüllungsstand │ Budget-Ende (Prognose) │
├─────────────────────────────────────────────────┤
│   100.0 h   │   45.5 h    │    45.5%       │ 15.12.2024 (45 Tage)   │
│             │  -54.5 h    │                │                        │
└─────────────────────────────────────────────────┘
```

---

## 🔢 **Prognose-Logik erklärt:**

### **Budget-Ende Berechnung:**
```python
# 1. Letzte 4 Wochen analysieren
recent_bookings = bookings_der_letzten_4_wochen

# 2. Durchschnitt berechnen
avg_hours_per_week = total_hours / 4_wochen

# 3. Verbleibende Stunden
remaining = sollstunden - ist_stunden

# 4. Prognose
weeks_until_empty = remaining / avg_hours_per_week
budget_ende = heute + weeks_until_empty
```

### **Wann zeigt es was:**

| Situation | Budget-Ende | Budget-Status |
|-----------|-------------|---------------|
| **Sollstunden > 0, Buchungen vorhanden, Budget offen** | "15.12.2024 (45 Tage)" | - |
| **Budget bereits erschöpft** | - | "⚠️ Erschöpft" |
| **Sollstunden = 0** | - | "Keine Prognose" |
| **Keine Buchungen (4 Wochen)** | - | "Keine Aktivität" |
| **Alle Stunden verbraucht** | - | "⚠️ Erschöpft" |

---

## 🛠️ **Troubleshooting:**

### **Problem: "Keine Prognose" wird angezeigt**

**Debug-Checkliste:**
```
✓ Sind Sollstunden gesetzt? (Tab Übersicht)
✓ Gibt es Buchungen im ausgewählten Projekt?
✓ Sind die Buchungen aktuell (letzte 4 Wochen)?
✓ Ist hours_column korrekt gewählt (FaktStd/Zeit)?
```

**Schnelle Lösung für TEST_MODE:**
Die Dummy-Daten sind veraltet (2024), während Sie in 2025 sind. Ich kann das beheben!

### **Problem: "Keine Aktivität"**

**Bedeutung:** 
In den letzten 4 Wochen wurden **0 Stunden** für dieses Projekt gebucht.

**Lösungen:**
- **TEST_MODE**: Dummy-Daten generieren aktuellere Zeitreihen
- **Produktiv**: Prüfen Sie, ob tatsächlich Buchungen vorhanden sind
- **Workaround**: Ändern Sie den Zeitraum-Filter auf ältere Monate

---

## 💡 **Verbesserungsvorschlag:**

Soll ich die Dummy-Daten so anpassen, dass sie **bis heute (September 2025)** reichen? Dann würde die Prognose sofort funktionieren!

**Zusätzlich könnte ich:**
1. **Fallback-Prognose** basierend auf Gesamtdurchschnitt (nicht nur 4 Wochen)
2. **Konfigurierbare Prognosezeitraum** (z.B. 2/4/8 Wochen wählbar)
3. **Warnungen** wenn Daten zu alt sind

Soll ich diese Verbesserungen implementieren?
