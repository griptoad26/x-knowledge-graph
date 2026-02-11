# 🧠 X Knowledge Graph v1.0.0

**Transform your X and Grok conversations into actionable intelligence.**

---

## ⭐ What's New in v1.0

- ✅ **Dark/Light Theme** - Toggle between dark and light modes
- ✅ **Amazon Product Linking** - Product mentions auto-link to Amazon
- ✅ **Todoist Export** - Sync actions to your task manager
- ✅ **Improved Action Extraction** - Better detection of tasks and follow-ups

---

## 🚀 Quick Start (Windows)

1. **Extract** all files from the archive
2. **Run** `XKnowledgeGraph.exe`
3. **Select** your X or Grok export folder
4. **View** your knowledge graph and action items

---

## 📦 What's Included

```
x-knowledge-graph-v1.0.0/
├── XKnowledgeGraph.exe     ← Main application (Windows)
├── README.txt             ← This file
├── VERSION.txt            ← Version info
├── frontend/              ← Web UI files
├── core/                 ← Parsers and exporters
│   ├── xkg_core.py       ← Main knowledge graph core
│   ├── amazon_product_linker.py  ← Amazon link generation
│   └── todoist_exporter.py      ← Todoist integration
└── test_data/           ← Sample exports
    └── grok_export/      ← Example Grok data
```

---

## 🎯 Features

### Conversation Intelligence
- Import **X (Twitter)** and **Grok** exports
- Extract **actions**, **follow-ups**, and **tasks**
- Link **related conversations** together
- Detect **products** and generate Amazon links

### Visualization
- **Knowledge Graph** - See how conversations connect
- **Timeline View** - Activity heatmap by date
- **Task Board** - Kanban view for action items
- **Topic Clusters** - Group by themes

### Export Options
- **Todoist** - Sync tasks with priority/due dates
- **CSV** - Spreadsheet export
- **JSON** - Raw data export

---

## 📖 Usage

### Import Your Data
1. Export your X data: Settings > Download your data
2. Export your Grok data: Grok > Export
3. Open X Knowledge Graph
4. Select the export folder

### Export to Todoist
```bash
# Set your Todoist API token
export TODOIST_API_TOKEN="your_token_here"

# Run with Todoist export
python main.py --export-todoist $TODOIST_API_TOKEN
```

### Export to JSON
```bash
python main.py --export-actions actions.json
python main.py --export-graph graph.json
```

---

## 🎨 Theme Toggle

Click the **moon/sun** icon in the header to switch themes:
- 🌙 **Dark** (default) - Easy on the eyes
- ☀️ **Light** - Classic appearance

Your preference is **saved automatically** and restored on next visit.

---

## 🛒 Amazon Product Links

When you mention products in your conversations:

| You Said | Auto-Generated Link |
|----------|---------------------|
| "buy a mouse" | [🛒 Amazon Search](https://amazon.com/s?k=mouse) |
| "get wireless headphones" | [🛒 Amazon Search](https://amazon.com/s?k=wireless+headphones) |

---

## 📊 Action Extraction Examples

Detected automatically:
- "TODO: review the proposal" → Task
- "need to follow up with John" → Follow-up
- "ASAP: send the email" → Urgent task
- "buy a new keyboard" → Task + Amazon link

---

## 🔧 Advanced Usage

### Self-Hosted (Python)
```bash
# Install dependencies
pip install -r requirements.txt

# Run web interface
python main.py

# Open browser to
# http://localhost:5000
```

### Build Windows EXE
```bash
# Using the build script
./build-xkg.sh

# Or manually
pip install pyinstaller
pyinstaller --onefile --windowed --name XKnowledgeGraph gui.py
```

---

## 📝 Action Priority Levels

Actions are automatically prioritized:

| Priority | Indicator | Color |
|----------|-----------|-------|
| 🔴 Urgent | "ASAP", "urgent", "EOD" | Red |
| 🟠 High | "important", "soon" | Orange |
| 🟡 Medium | Default | Yellow |
| 🟢 Low | "sometime", "maybe" | Green |

---

## 🤝 Support

**Questions or issues?**

- 📧 **Email:** griptoad.26@gmail.com
- 🐦 **X/Twitter:** @BitminersSD
- 💬 **GitHub:** Report issues on GitHub

---

## 📜 License

MIT License - Use freely, modify as needed.

---

## 🙏 Credits

Built with:
- Flask (web framework)
- NetworkX (graph visualization)
- Pandas (data processing)

---

## 📊 Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | 2026-02-10 | Dark mode, Amazon links, Todoist export |
| v0.3.22 | 2026-02-08 | Grok recursive parsing |
| v0.3.0 | 2026-02-04 | Initial release |

---

*X Knowledge Graph v1.0.0 - Never lose track of your conversations.*
