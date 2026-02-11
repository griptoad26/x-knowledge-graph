# 🧠 X Knowledge Graph v0.4.2

## Quick Start (Windows)

### Option 1: Quick Run (No Build!)
```cmd
quick-run.bat
```
Then select:
- [1] Desktop App (GUI)
- [2] Web App (browser opens)

### Option 2: Build Standalone .exe (For Distribution)
```cmd
build.bat
```
Creates a standalone `dist/XKnowledgeGraph.exe` - no Python required!

---

## 📦 What's Included

```
x-knowledge-graph-v0.4.2/
├── quick-run.bat     ← Double-click to run!
├── build.bat         ← Build standalone .exe
├── gui.py            ← Desktop app ⭐ FIXED
├── main.py           ← Web app
├── requirements.txt  ← Python dependencies
├── README.md         ← This file
├── core/             ← Core modules (action extraction, Amazon links)
├── frontend/         ← Web UI
└── test_data/        ← Sample Grok export
```

---

## ✅ Features

- **Action Extraction** - Detect TODOs, follow-ups, urgent tasks
- **Amazon Links** - Auto-link products mentioned
- **Todoist Export** - Sync to task manager
- **Dark Theme** - Easy on the eyes

---

## 🚀 How to Use

### Desktop App
```cmd
python gui.py
```

### Web App
```cmd
python main.py
# Opens: http://localhost:5000
```

### Export to Todoist
```cmd
python main.py --export-todoist YOUR_API_TOKEN
```

---

## 📋 Requirements

- Python 3.9-3.11 (python.org/downloads)
- Windows 10/11

---

## 📞 Support

- Email: griptoad.26@gmail.com
- X: @BitminersSD

---

*X Knowledge Graph - Never lose track of your conversations*
