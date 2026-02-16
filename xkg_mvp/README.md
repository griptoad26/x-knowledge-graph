# xkg_mvp - Grok Content Converter

**Version:** v0.0.1  
**Status:** PLANNED  
**Parent Project:** x-knowledge-graph

---

## Overview

Extract Grok conversations → Convert to Reddit-style searchable content → Export to browser extensions/reading apps.

## Problem Statement

Current browser extensions require manual "open each file" to copy conversation content. Users waste hours exporting AI chats one-by-one.

## Solution

Automated extraction + formatting with:
- Reddit-style threaded conversation viewer
- Multiple export formats (PDF, HTML, Markdown)
- Browser extension integration (Notion, Evernote, Matter, Omnivore)

## Features (v0.0.1)

### Core
- [ ] Grok JSON file import (drag & drop)
- [ ] Threaded conversation display
- [ ] Search within conversations
- [ ] Markdown export

### Extended (v0.0.2+)
- [ ] PDF export
- [ ] HTML export
- [ ] Browser extension (Chrome/Firefox)
- [ ] Notion integration
- [ ] Evernote integration
- [ ] Matter/Omnivore sync

## Architecture

```
xkg_mvp/
├── frontend/           # Web UI
│   ├── index.html     # Main interface
│   ├── css/           # Styles
│   └── js/            # Scripts
├── core/              # Python processing
│   ├── grok_parser.py  # Grok JSON extraction
│   ├── converter.py   # Reddit-style formatting
│   └── exporter.py    # Export handlers
├── static/            # Static assets
└── main.py            # Flask app
```

## Rollback Strategy

All xkg_mvo code designed to merge back into x-knowledge-graph:
- `core/grok_parser.py` → merges into `core/grok_export/`
- `frontend/conversation-view/` → merges into `frontend/`
- `core/exporter.py` → enhances `core/pkm_exporter.py`

## Development Phases

| Phase | Version | Features |
|-------|---------|----------|
| 1 | v0.0.1 | Grok import + Markdown export |
| 2 | v0.0.2 | PDF/HTML export |
| 3 | v0.0.3 | Browser extension stub |
| 4 | v0.0.4 | Notion/Evernote integration |

## MVP Launch Checklist

- [ ] Grok parser validates JSON structure
- [ ] Threaded view renders correctly
- [ ] Search finds messages
- [ ] Markdown exports readable
- [ ] Sample exports tested
- [ ] Documentation complete
- [ ] Deployed to subdirectory: `/mvp/`

## Related Projects

- **Parent:** `x-knowledge-graph` - Full feature set
- **Parser:** `core/grok_export/` - Shared Grok parsing
- **Export:** `core/pkm_exporter/` - Shared PKM export

## Market Opportunity

**Target Users:**
- AI power users with hundreds of conversations
- Researchers archiving AI interactions
- Content creators repackaging AI chats

**Competitors:**
- ChatGPT Exporter (Chrome extension)
- Claude Exporter (Chrome extension)
- OneClickGPT

**Differentiation:**
- Multi-platform (Grok + ChatGPT + Claude + Gemini)
- Reddit-style threading
- Built-in search
- Batch export

---

*Created: 2026-02-16*
*Target: v0.0.1 MVP launch*
