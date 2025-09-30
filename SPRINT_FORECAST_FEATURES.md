# 🚀 Sprint-basierte Forecast-Features - Übersicht

## ✅ **Alle Features implementiert!**

### **1. Sprint-basiertes Forecasting** 

**Logik:**
- **4 Sprints** à 2 Wochen (8 Wochen historische Daten)
- **Gewichtete Analyse**: Letzte 2 Wochen = 40%, dann 30%, 20%, 10%
- **Automatische Berechnung**: Velocity aus gewichtetem Sprint-Durchschnitt

**Verwendung:**
```
Tab "📈 Zeitreihen" öffnen
→ Projekt auswählen
→ System berechnet automatisch Sprint-Velocity
→ 3 Szenarien werden angezeigt
```

---

### **2. Drei Prognose-Szenarien**

| Szenario | Wahrscheinlichkeit | Berechnung | Use Case |
|----------|-------------------|------------|----------|
| 🟢 **Optimistisch** | 90% | +1.5σ Velocity | Best Case, Team produktiv |
| 🟡 **Realistisch** | 50% | Gewichteter Ø | Most Likely, aktueller Trend |
| 🔴 **Pessimistisch** | 10% | -1.5σ Velocity | Worst Case, Blocker/Urlaube |

**Was wird angezeigt:**
- **Budget-Ende Datum** für jedes Szenario
- **Tage verbleibend** bis Budget-Erschöpfung
- **Sprints verbleibend** (in 2-Wochen-Einheiten)
- **Stunden/Sprint** Annahme

---

### **3. Manuelle Prognose-Override**

**Wann verwenden:**
- Geplante Team-Änderungen (neue Mitarbeiter, Abgänge)
- Bekannte Urlaube/Feiertage
- Scope-Änderungen
- Historische Daten nicht repräsentativ

**So funktioniert's:**
```
1. Checkbox "📝 Manuelle Prognose aktivieren" ✅
2. "Erwartete Std/Sprint" eingeben (z.B. 60h statt auto 75h)
3. Begründung eingeben: "Team-Urlaub im Oktober"
4. "💾 Speichern" klicken
→ Prognose wird persistiert und bei nächstem Besuch geladen
```

**Wo gespeichert:**
- `cache/forecast_{projekt}.json` (Projekt-Level)
- `cache/forecast_{projekt}_{activity}.json` (Activity-Level)

---

### **4. Velocity-Trend-Analyse**

**Automatische Erkennung:**
- 📈 **Steigend** (+2h/Sprint): "Team wird produktiver!"
- 📊 **Stabil** (-2 bis +2h): Normalbetrieb
- 📉 **Fallend** (-2h/Sprint): "⚠️ Trend-Warnung: Team überlastet?"

**Verwendung:**
System zeigt automatisch Warnungen, wenn Trends erkannt werden.

---

### **5. Szenario-Visualisierung**

**Burn-down Chart mit 3 Linien:**
- **Grau gestrichelt**: Sollstunden (Budget)
- **Blau durchgezogen**: Ist-Stunden (historisch)
- **Grün gepunktet**: Optimistisches Ende
- **Orange durchgezogen**: Realistisches Ende  
- **Rot gepunktet**: Pessimistisches Ende

**Interaktiv:**
- Hover zeigt Datum + Stunden
- X-Marker zeigen Budget-Ende pro Szenario
- Zoom/Pan verfügbar

---

### **6. Sprint-Details Tabelle**

**Expandable Ansicht zeigt:**
```
┌─────────────────────────────────────────────────┐
│ Sprint      │ Stunden │ Start      │ Ende       │ Gewicht │
├─────────────────────────────────────────────────┤
│ Aktuell     │ 85.3h   │ 16.09.2025 │ 30.09.2025 │ 40%     │
│ Sprint -1   │ 72.1h   │ 02.09.2025 │ 15.09.2025 │ 30%     │
│ Sprint -2   │ 68.5h   │ 19.08.2025 │ 01.09.2025 │ 20%     │
│ Sprint -3   │ 75.2h   │ 05.08.2025 │ 18.08.2025 │ 10%     │
└─────────────────────────────────────────────────┘

Gewichteter Ø: 77.4h/Sprint
```

---

## 🧪 **TEST-MODE Funktionalität**

### **Sprint-Dummy-Daten:**
- ✅ **8 Wochen** aktuelle Daten (bis heute)
- ✅ **4 Sprints** mit realistischer Velocity-Variation
- ✅ **Mo-Fr Buchungen** (keine Wochenenden)
- ✅ **Velocity schwankt** zwischen 65-95h pro Sprint
- ✅ **Tages-Varianz** 60-140% vom Durchschnitt

**Beispiel-Output:**
```
Sprint 0 (aktuell): 82.3h (40% Gewicht)
Sprint -1: 75.1h (30% Gewicht)
Sprint -2: 88.7h (20% Gewicht)
Sprint -3: 71.2h (10% Gewicht)
→ Gewichteter Ø: 79.8h/Sprint
```

---

## 📊 **Metriken erklärt:**

### **Basis-Velocity:**
Gewichteter Durchschnitt über 4 Sprints:
```
Velocity = (Sprint0×40% + Sprint1×30% + Sprint2×20% + Sprint3×10%)
```

### **Prognose-Sicherheit:**
Basiert auf Varianz zwischen Sprints:
- **80-100%**: Sehr konstante Sprints → hohe Sicherheit
- **60-80%**: Moderate Schwankungen → mittlere Sicherheit  
- **<60%**: Hohe Varianz → niedrige Sicherheit

### **Budget-Ende Berechnung:**
```
Verbleibende Stunden = Sollstunden - Ist-Stunden
Sprints benötigt = Verbleibend / Velocity
Tage = Sprints × 14
Budget-Ende = Heute + Tage
```

---

## 🎯 **Anwendungsbeispiele:**

### **Beispiel 1: Projekt läuft gut**
```
Sollstunden: 200h
Ist: 120h
Verbleibend: 80h
Velocity: 40h/Sprint

→ Optimistisch: 1.3 Sprints (18 Tage) → 18.10.2025
→ Realistisch: 2.0 Sprints (28 Tage) → 28.10.2025
→ Pessimistisch: 2.7 Sprints (38 Tage) → 07.11.2025
```

### **Beispiel 2: Budget-Warnung**
```
Sollstunden: 100h
Ist: 95h
Verbleibend: 5h
Velocity: 20h/Sprint

→ Alle Szenarien zeigen: < 1 Sprint verbleibend
→ Budget-Status: ⚠️ Kritisch
→ Empfehlung: Nachverhandlung oder Scope-Reduktion
```

### **Beispiel 3: Manuelle Override nötig**
```
Automatische Velocity: 80h/Sprint
ABER: Team-Urlaub im Oktober (2 Wochen)

→ Manuelle Prognose: 40h/Sprint
→ Begründung: "Oktober Team-Urlaub"
→ Speichern
→ Realistische Prognose wird angepasst
```

---

## 🔧 **Troubleshooting:**

### **"Keine Prognose möglich"**
**Ursachen:**
1. Sollstunden = 0 → **Lösung**: Sollstunden im Tab "Übersicht" setzen
2. Keine Buchungen → **Lösung**: Warten auf erste Buchungen oder TEST_MODE aktivieren
3. Alle Buchungen älter als 8 Wochen → **Lösung**: Dummy-Daten neu generieren

### **"Insufficient data"**
**Ursache**: Weniger als 2 Sprints mit Buchungen
**Lösung**: 
- Warten auf mehr historische Daten
- Fallback auf Gesamtdurchschnitt (wird automatisch verwendet)

### **"Prognose-Sicherheit < 50%"**
**Ursache**: Hohe Varianz zwischen Sprints
**Empfehlung**:
- Manuelle Override mit realistischeren Werten
- Ursachen für Schwankungen analysieren
- Mehr Sprints abwarten für stabilere Prognose

---

## 🚀 **Neue Features testen:**

```bash
# Lokaler Test:
python -m streamlit run app.py

# TEST Deploy:
docker-compose -f docker-compose.test.yml up -d
# → http://localhost:8502

# Checklist:
# 1. Tab "Zeitreihen" öffnen ✅
# 2. Sollstunden im Tab "Übersicht" setzen (z.B. 100h) ✅
# 3. Zurück zu "Zeitreihen" ✅
# 4. 3 Szenario-Karten werden angezeigt ✅
# 5. Szenario-Chart mit farbigen Linien ✅
# 6. Sprint-Details expandieren → Tabelle mit 4 Sprints ✅
# 7. Manuelle Override testen ✅
# 8. Velocity-Trend-Warnung sichtbar (falls Trend erkannt) ✅
```

---

## 📈 **Erwartete Verbesserungen:**

### **Vorher (einfaches Burndown):**
- ✅ Einzelne Prognose-Linie
- ❌ Keine Unsicherheits-Bereiche
- ❌ Keine Sprint-Analyse
- ❌ Kein manueller Override

### **Nachher (Sprint-Szenarien):**
- ✅ **3 Szenarien** mit Konfidenz-Leveln
- ✅ **Sprint-gewichtete** Berechnung (aktuell = wichtiger)
- ✅ **Trend-Erkennung** (steigend/fallend)
- ✅ **Manuelle Overrides** mit Persistierung
- ✅ **Sprint-Velocity Chart** für Deep-Dive
- ✅ **Prognose-Sicherheit** als Metrik

---

## 💾 **Persistierte Daten:**

**Forecast-Overrides:**
```json
// cache/forecast_P24ABC01.json
{
  "hours_per_sprint": 60.0,
  "reason": "Team-Urlaub im Oktober",
  "updated_at": "2025-09-30T12:00:00",
  "updated_by": "admin@company.com"
}
```

**Target Hours:**
```json
// cache/targets_P24ABC01_Implementierung.json  
{
  "project": "P24ABC01",
  "activity": "Implementierung",
  "target_hours": 120.0,
  "timestamp": "2025-09-30T12:00:00"
}
```

---

## 🎉 **Das neue System bietet:**

1. **Bessere Entscheidungsgrundlage** durch 3 Szenarien
2. **Frühwarnung** bei sinkender Velocity
3. **Planbare Prognosen** mit realistischen Ranges
4. **Manuelle Anpassung** für bekannte Änderungen
5. **Transparenz** durch Sprint-Details

**Die Budget-Ende und Budget-Status Felder sollten jetzt korrekt funktionieren!** 🎯
