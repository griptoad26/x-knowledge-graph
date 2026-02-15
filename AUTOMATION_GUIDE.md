# X Knowledge Graph - Automation Guide

## Complete Automation Setup for VPS

This document provides step-by-step instructions for setting up fully automated validation, improvement, and distribution.

---

## Quick Start

### One-Line Automation Startup

```powershell
cd C:\Projects\x-knowledge-graph
python auto-improve.py
```

This runs the complete pipeline:
1. Pull latest code
2. Run 19 graph validation tests
3. Run 17 core tests
4. Run full API validation
5. **Create distribution** (only if all tests pass)
6. Commit distribution

---

## Sample Data Being Validated

### X Export (`test_data/x_export/tweet.js`)
```
5 tweets processed:
1. "Working on a new project. Need to finish the API integration by Friday."
2. "TODO: Review the documentation and update the examples. This is urgent..."
3. "Remember to schedule a meeting with the design team..."
4. "Going to refactor the authentication module next week..."
5. "Don't forget to backup the database before the maintenance..."

Expected Results:
- 5 tweet nodes
- 7 action items extracted
- Topics: technology, business, personal, finance, health, social
```

### Grok Export (`test_data/grok_export/posts.json`)
```
10 posts processed:
1. "Just shipped the new feature to production. Need to monitor..."
2. "TODO: Update the API documentation for the new endpoints..."
3. "Remember to buy a new keyboard for the workstation..."
4. "Going to schedule a 1:1 with the team lead..."
5. "Need to research pricing models for the new SaaS product..."
6. "ASAP: Fix the login bug that's affecting 5% of users..."
7. "Going to refactor the database queries to improve..."
8. "Don't forget to renew the domain names..."
9. "Need to set up automated testing for the CI/CD pipeline..."
10. "Remember to order office supplies..."

Expected Results:
- 10 grok nodes
- 15 action items extracted
- Topics: technology, business, personal, finance, health, social, learning
```

### Combined Export
```
Total: 15 items (5 X + 10 Grok)
- 22+ action items extracted
- All topics clustered
- Full graph with edges
```

---

## Validation Tests

### Graph Population Tests (3 tests)
| Test | Validates |
|------|-----------|
| X Export Populates Graph | 5 tweets → 5 nodes, 7+ actions |
| Grok Export Populates Graph | 10 posts → 10 nodes, 15+ actions |
| Combined Export Populates Graph | 15 items → 15 nodes |

### Action Extraction Tests (3 tests)
| Test | Validates |
|------|-----------|
| Actions Extracted from X | Priority labels, task keywords |
| Actions Extracted from Grok | ASAP → urgent, TODO → high |
| Action Content | Text present, meaningful content |

### Topic Clustering Tests (3 tests)
| Test | Validates |
|------|-----------|
| Topics from X | 5+ unique topics clustered |
| Topics from Grok | 5+ unique topics clustered |
| Topics Combined | Unified topic map |

### Graph Structure Tests (4 tests)
| Test | Validates |
|------|-----------|
| Valid D3 Structure | nodes + edges present |
| Node Types | tweet, grok, action, topic |
| Edge Connections | source/target valid |
| Node Content | text/label accessible |

### Performance Tests (4 tests)
| Test | Target |
|------|--------|
| X Parse | < 2 seconds |
| Grok Parse | < 3 seconds |
| Combined Parse | < 5 seconds |
| Graph Export | < 1 second |

### Flask API Tests (5 tests)
| Test | Endpoint |
|------|----------|
| Health Check | /api/health |
| Parse X | /api/parse-export |
| Parse Grok | /api/parse-export |
| Get Graph | /api/graph |
| Get Actions | /api/actions |

**Total: 19 graph validation tests + 17 core tests + 5 API tests = 41 tests**

---

## Automation Commands

### Development (Manual)
```powershell
# Run graph tests
pytest tests/test_graph_validation.py -v

# Run core tests
pytest tests/test_core.py -v

# Run full validation
python validate.py

# Build EXE
build.bat
```

### Automation (Scheduled)
```powershell
# Full automation with distribution
python auto-improve.py

# Tests only
python auto-improve.py --test-only

# Distribution only
python auto-improve.py --dist-only
```

### Scheduled Task (Windows)
```powershell
# Create scheduled task for daily builds
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\Projects\x-knowledge-graph\auto-improve.py" -WorkingDirectory "C:\Projects\x-knowledge-graph"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "XKG-AutoBuild" -Action $action -Trigger $trigger -RunLevel Highest
Start-ScheduledTask -TaskName "XKG-AutoBuild"
```

---

## Distribution Creation

When **all tests pass**, the system automatically:

1. **Creates distribution directory:**
   ```
   distributions/
   └── x-knowledge-graph-v0.4.33/
       ├── main.py
       ├── core/
       ├── frontend/
       ├── VERSION.txt
       ├── requirements.txt
       ├── build.bat
       ├── validate.py
       ├── README.md
       └── ...
   ```

2. **Creates tar archive:**
   ```
   distributions/x-knowledge-graph-v0.4.33.tar
   ```

3. **Generates checksums:**
   ```
   distributions/checksums.txt
   SHA256 hashes for all files
   ```

4. **Commits to git:**
   ```
   git commit -m "Distribution v0.4.33 - 2026-02-14"
   ```

---

## Files Created

| File | Purpose |
|------|---------|
| `auto-improve.py` | Main automation script |
| `validate.py` | Comprehensive validation |
| `test_graph_validation.py` | 19 graph tests |
| `test_core.py` | 17 core tests |
| `BUILD_SETUP.md` | Build setup guide |
| `PRODUCTION_BUILD.md` | Production process |

---

## Troubleshooting

### Tests Failing
```powershell
# Pull latest and retry
git pull
pytest tests/ -v

# Check specific test
pytest tests/test_graph_validation.py::TestGraphPopulation::test_x_export_populates_graph -v
```

### Distribution Not Created
- Check that ALL tests pass (41 tests)
- Distribution only created on 100% success
- Review validation output for failures

### GitHub Upload Failed
- Token may be expired or insufficient scope
- Token needs `gist` scope for Gist uploads

---

## Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SCHEDULED TASK (Daily @ 2AM)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. GIT PULL                                                             │
│     └─→ Fetch latest from GitHub                                         │
│                                                                          │
│  2. GRAPH VALIDATION (19 tests)                                          │
│     ├─ X Export → 5 tweets, 7 actions, 5+ topics                        │
│     ├─ Grok Export → 10 posts, 15 actions, 5+ topics                     │
│     └─ Combined → 15 items, full graph                                   │
│                                                                          │
│  3. CORE TESTS (17 tests)                                                │
│     ├─ Parsing, actions, topics, flows                                   │
│     ├─ Performance (<2s, <3s, <5s)                                       │
│     └─ Edge cases                                                        │
│                                                                          │
│  4. FLASK API TESTS (5 tests)                                           │
│     ├─ Health check                                                      │
│     ├─ Parse X endpoint                                                  │
│     ├─ Parse Grok endpoint                                               │
│     ├─ Graph endpoint                                                    │
│     └─ Actions endpoint                                                  │
│                                                                          │
│  5. DECISION: ALL TESTS PASS?                                            │
│     ├─ NO → Stop (alert human)                                           │
│     └─ YES → Continue                                                    │
│                                                                          │
│  6. CREATE DISTRIBUTION                                                  │
│     ├─ Copy files to distributions/x-knowledge-graph-v0.4.33/            │
│     ├─ Create tar archive                                                │
│     ├─ Generate SHA256 checksums                                          │
│     └─ Git commit                                                        │
│                                                                          │
│  7. EXIT                                                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **On VPS, clone and setup:**
   ```powershell
   cd C:\Projects
   git clone https://github.com/griptoad26/x-knowledge-graph.git
   cd x-knowledge-graph
   pip install -r requirements.txt
   ```

2. **Run full automation:**
   ```powershell
   python auto-improve.py
   ```

3. **Check distribution created:**
   ```powershell
   dir distributions\
   ```

---

## Current Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| Graph Population | 3 | ✅ 3/3 pass |
| Action Extraction | 3 | ✅ 3/3 pass |
| Topic Clustering | 3 | ✅ 3/3 pass |
| Graph Structure | 4 | ✅ 4/4 pass |
| Performance | 4 | ✅ 4/4 pass |
| Sample Data | 2 | ✅ 2/2 pass |
| **Total** | **19** | **✅ 19/19 pass** |

---

## Need Help?

- **Tests failing?** Run `pytest tests/test_graph_validation.py -v` to see details
- **Distribution not created?** Check that all 19 tests pass first
- **GitHub issues?** Verify token has `gist` scope
