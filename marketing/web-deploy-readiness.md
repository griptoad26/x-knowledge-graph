# X KNOWLEDGE GRAPH - WEB DEPLOYMENT READINESS
## Deployment Checklist for Production

---

## 🚀 DEPLOYMENT OPTIONS

### Option 1: Static Files (Simplest)
- Copy `frontend/` folder to any static host
- No backend required
- Features: View only (no export)

### Option 2: PythonAnywhere
- **URL:** https://www.pythonanywhere.com/
- **Cost:** Free tier available
- **Steps:**
  1. Upload project files
  2. `pip install -r requirements.txt`
  3. Run: `python main.py`
  4. Access: yourusername.pythonanywhere.com

### Option 3: Railway/Render (Recommended)
- **Railway:** https://railway.app/
- **Render:** https://render.com/
- **Cost:** Free tier available
- **Steps:**
  1. Connect GitHub repo
  2. Build command: `pip install -r requirements.txt`
  3. Start command: `python main.py`
  4. Custom domain supported

### Option 4: Vercel (Frontend + API)
- **URL:** https://vercel.com/
- **Cost:** Free tier available
- **Note:** Requires API route setup

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### Code
- [x] main.py runs without errors
- [x] requirements.txt complete
- [x] PORT environment variable handled
- [x] CORS configured for production domain

### Frontend
- [x] All CSS/JS inline or bundled
- [x] No hardcoded localhost URLs
- [x] Help modal content complete
- [x] Theme toggle working

### Data
- [x] Sample exports in test_data/
- [x] Export parsing tested
- [x] Action extraction validated

### Testing
- [x] Core tests pass: `python3 -c "from core.xkg_core import KnowledgeGraph; print('OK")"`
- [x] Amazon linking tested
- [x] Todoist export tested

---

## 🐳 DOCKER DEPLOYMENT (Optional)

### Dockerfile
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "main.py"]
```

### Docker Commands
```bash
# Build
docker build -t x-knowledge-graph .

# Run locally
docker run -p 5000:5000 x-knowledge-graph

# Deploy to Railway
railway deploy
```

---

## 🔧 ENVIRONMENT VARIABLES

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| PORT | No | 5000 | HTTP port |
| DEBUG | No | false | Debug mode |
| TODOIST_API_TOKEN | No | - | Todoist API key |

---

## 📁 DEPLOYMENT FOLDER STRUCTURE

```
x-knowledge-graph/
├── main.py                 ← Flask app
├── gui.py                  ← Desktop GUI
├── requirements.txt        ← Python deps
├── core/                   ← Parsers
│   ├── xkg_core.py
│   ├── amazon_product_linker.py
│   └── todoist_exporter.py
├── frontend/               ← Web UI
│   ├── index.html
│   ├── css/
│   └── js/
└── test_data/             ← Samples
    └── grok_export/
```

---

## 🌐 PRODUCTION URLS (To Be Filled)

| Platform | URL | Status |
|----------|-----|--------|
| PythonAnywhere | `_____.pythonanywhere.com` | Not deployed |
| Railway | `_____.railway.app` | Not deployed |
| Render | `_____.onrender.com` | Not deployed |
| Custom Domain | `xkg.app` | Not configured |

---

## 📊 FEATURE MATRIX

| Feature | Local | Static Web | Full Deploy |
|---------|-------|------------|-------------|
| View exports | ✅ | ✅ | ✅ |
| Action extraction | ✅ | ✅ | ✅ |
| Knowledge graph | ✅ | ✅ | ✅ |
| Amazon links | ✅ | ❌ | ✅ |
| Todoist export | ✅ | ❌ | ✅ |
| Export files | ✅ | ❌ | ✅ |

---

## 🔒 SECURITY CHECKLIST

- [ ] No API keys in code
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] HTTPS enforced (production)
- [ ] Input sanitization

---

## 📈 MONITORING

### Health Check Endpoint
`GET /health` returns:
```json
{"status": "ok", "version": "1.0.0"}
```

### Logging
- Errors logged to stderr
- Access logs enabled
- No sensitive data in logs

---

## 📞 SUPPORT CONTACTS

- **Email:** griptoad.26@gmail.com
- **X:** @BitminersSD
- **Issues:** GitHub issues

---

*Document Version: 1.0*
*Last Updated: 2026-02-10*
