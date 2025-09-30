# 🔗 Azure DevOps Dashboard Integration

## 🎯 **Iframe Embedding Support aktiviert!**

Das Streamlit Dashboard unterstützt jetzt **iframe embedding** für Azure DevOps Dashboards.

## ⚙️ **Aktivierte Konfigurationen:**

### **Streamlit Settings (alle Modi):**
- ✅ `enableCORS = true` - Cross-Origin Requests erlaubt
- ✅ `enableXsrfProtection = false` - XSRF-Schutz deaktiviert für iframe
- ✅ `embedOptions = ["frameless"]` - Optimiert für iframe embedding
- ✅ `allowRunOnSave = false` - Verhindert Auto-Reload in iframe

### **HTTP Headers:**
- ✅ **X-Frame-Options**: `ALLOWALL` oder `SAMEORIGIN`
- ✅ **CORS Headers**: Aktiviert für cross-origin requests
- ✅ **Content Security Policy**: iframe-freundlich

## 🚀 **Azure DevOps Integration:**

### **Schritt 1: Dashboard Container starten**
```bash
# Produktions-Container mit iframe Support
docker-compose up -d
# → Dashboard läuft auf: http://your-server:8501

# Oder Test-Container
docker-compose -f docker-compose.test.yml up -d  
# → Dashboard läuft auf: http://your-server:8502
```

### **Schritt 2: Azure DevOps Dashboard konfigurieren**

1. **Azure DevOps öffnen** → Ihr Projekt
2. **Overview** → **Dashboards** 
3. **Edit Dashboard** → **Add Widget**
4. **"Web page"** oder **"Embedded Webpage"** Widget wählen
5. **URL eingeben**: `http://your-server:8501`
6. **Size anpassen** (z.B. 12x8 oder Full Width)
7. **Save**

### **Schritt 3: Test der iframe Integration**

**Lokal testen:**
```html
<!-- Test iframe lokal -->
<iframe 
  src="http://localhost:8501" 
  width="100%" 
  height="800"
  frameborder="0"
  allowfullscreen>
</iframe>
```

## 🔧 **Troubleshooting:**

### **Problem: "This content cannot be displayed in a frame"**

**Lösung 1 - Streamlit Konfiguration prüfen:**
```bash
# Container Config prüfen
docker exec sql-server-dashboard cat /home/streamlit/.streamlit/config.toml

# Sollte enthalten:
# enableCORS = true
# enableXsrfProtection = false
# embedOptions = ["frameless"]
```

**Lösung 2 - Container neu bauen:**
```bash
# Mit aktualisierter iframe-Konfiguration
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### **Problem: Azure DevOps zeigt "Access Denied"**

**Lösung - URL-Parameter hinzufügen:**
```
# Standard URL
http://your-server:8501

# Mit embed Parameter (falls nötig)
http://your-server:8501?embed=true

# Mit embedded Parameter für Streamlit
http://your-server:8501?embedded=true
```

### **Problem: CORS Errors**

**Lösung - Environment Variables setzen:**
```yaml
environment:
  - STREAMLIT_SERVER_ENABLE_CORS=true
  - STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
  - STREAMLIT_SERVER_ALLOW_ORIGIN_LIST=["https://dev.azure.com", "https://your-org.visualstudio.com"]
```

## 📊 **Azure DevOps Widget Konfiguration:**

### **Empfohlene Widget-Settings:**
- **Widget Type**: "Embedded Webpage" oder "Web page"
- **URL**: `http://your-dashboard-server:8501`
- **Refresh Rate**: 300 seconds (5 Minuten)
- **Size**: Large (12 columns x 8 rows) oder Full Width
- **Title**: "SQL Server Dashboard - Zeiterfassung"

### **Advanced Settings:**
```json
{
  "url": "http://your-server:8501",
  "height": "800px",
  "refreshRate": 300,
  "allowFullScreen": true,
  "sandbox": "allow-scripts allow-same-origin allow-forms"
}
```

## 🎯 **Optimierungen für Azure DevOps:**

### **Dashboard Layout anpassen:**
- **Compact Mode**: Weniger Whitespace für iframe
- **Auto-refresh**: Dashboard aktualisiert sich automatisch
- **Responsive**: Passt sich an iframe-Größe an

### **URL-Parameter für iframe Optimierung:**
```
# Ohne Sidebar (mehr Platz)
http://your-server:8501?sidebar=false

# Embedded Mode
http://your-server:8501?embedded=true

# Kombiniert
http://your-server:8501?embedded=true&sidebar=false
```

## 🔍 **Validierung:**

### **iframe Test (HTML):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Test</title>
</head>
<body>
    <h1>Azure DevOps Dashboard Integration Test</h1>
    <iframe 
        src="http://localhost:8501" 
        width="1200" 
        height="800"
        frameborder="0"
        style="border: 1px solid #ccc;">
        Ihr Browser unterstützt keine iframes.
    </iframe>
</body>
</html>
```

### **CORS Test:**
```bash
# Test CORS Headers
curl -H "Origin: https://dev.azure.com" \
     -H "Access-Control-Request-Method: GET" \
     -v http://your-server:8501
```

## 📋 **Azure DevOps Deployment Checklist:**

- [ ] Container mit iframe-Support gestartet
- [ ] CORS aktiviert (`enableCORS = true`)
- [ ] XSRF-Protection deaktiviert 
- [ ] Dashboard via URL erreichbar
- [ ] Azure DevOps Widget erstellt
- [ ] iframe Test erfolgreich
- [ ] Auto-refresh funktioniert

## 🎉 **Fertig!**

Ihr SQL Server Dashboard ist jetzt **vollständig iframe-kompatibel** und bereit für die Integration in Azure DevOps Dashboards!

**URL für Azure DevOps**: `http://your-server:8501`
