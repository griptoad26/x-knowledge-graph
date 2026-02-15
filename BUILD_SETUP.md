# X Knowledge Graph - Windows Build Setup Guide

## Complete Step-by-Step Automation Setup

This guide walks you through setting up the fully automated build pipeline on your Windows VPS.

---

## Prerequisites

### What You Need
- [ ] Windows 10/11 VPS or machine
- [ ] Python 3.11+ installed
- [ ] Git installed
- [ ] 500MB free disk space
- [ ] GitHub account with repo access

### Check Python Version
```powershell
python --version
```
Should show `Python 3.11.x` or higher.

---

## Step 1: Clone Repository

```powershell
cd C:\
mkdir Projects
cd Projects
git clone https://github.com/griptoad26/x-knowledge-graph.git
cd x-knowledge-graph
```

---

## Step 2: Setup Python Environment

### Option A: Use System Python
```powershell
pip install --upgrade pip
pip install pyinstaller flask flask-cors requests pytest
```

### Option B: Create Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install --upgrade pip
pip install pyinstaller flask flask-cors requests pytest
```

---

## Step 3: Verify Installation

```powershell
python --version
pyinstaller --version
pytest --version
```

Expected output:
```
Python 3.11.x
5.x.x
7.x.x
```

---

## Step 4: Run Tests (First Time)

```powershell
cd C:\Projects\x-knowledge-graph
pytest tests/ -v
```

Expected output:
```
17 passed in 0.16s
```

If tests pass, continue. If tests fail, fix issues before proceeding.

---

## Step 5: Build Windows EXE

```powershell
cd C:\Projects\x-knowledge-graph
build.bat
```

This will:
1. Clean previous builds
2. Install dependencies
3. Build EXE with PyInstaller
4. Generate SHA256 checksum

**Expected output:**
```
X Knowledge Graph - Windows Build
Version: 0.4.33

Building EXE with PyInstaller...

========================================
  BUILD SUCCESSFUL
========================================

File: dist\XKnowledgeGraph.exe
Size: XX.XX MB

Checksum saved to: dist\checksum.txt
```

---

## Step 6: Test the EXE

```powershell
cd C:\Projects\x-knowledge-graph\dist
.\XKnowledgeGraph.exe
```

The app should open in your default browser at `http://localhost:5000`.

To exit: Press `Ctrl+C` in the terminal.

---

## Step 7: Validate the Build

```powershell
cd C:\Projects\x-knowledge-graph
python validate.py
```

Expected output:
```
8 tests passed, 0 failed
```

---

## Step 8: Setup Automation

### Option A: Automated Build Script (Recommended)

```powershell
cd C:\Projects\x-knowledge-graph
python auto-build.py
```

This runs the full pipeline:
1. Pull latest code
2. Run tests
3. Run validation
4. Build EXE
5. Test EXE
6. Create release notes

### Option B: Scheduled Task (Fully Automated)

```powershell
# Create scheduled task to run every day at 2 AM
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\Projects\x-knowledge-graph\auto-build.py" -WorkingDirectory "C:\Projects\x-knowledge-graph"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "XKG-Build" -Action $action -Trigger $trigger -RunLevel Highest -Description "Daily XKG build"
Start-ScheduledTask -TaskName "XKG-Build"
```

---

## Step 9: Upload Release (Optional)

When ready to publish:

```powershell
# Tag and push version
git add -A
git commit -m "Release v0.4.33"
git tag v0.4.33
git push && git push --tags
```

Then create a GitHub Release:
1. Go to: https://github.com/griptoad26/x-knowledge-graph/releases
2. Click "Draft new release"
3. Select tag v0.4.33
4. Upload:
   - `dist/XKnowledgeGraph.exe`
   - `dist/checksum.txt`
   - `dist/RELEASE_NOTES.md`
5. Click "Publish release"

---

## Quick Reference Commands

```powershell
# Setup (one-time)
git clone https://github.com/griptoad26/x-knowledge-graph.git
cd x-knowledge-graph
pip install pyinstaller flask flask-cors requests pytest

# Daily development
pytest tests/ -v              # Run tests
build.bat                     # Build EXE
python validate.py            # Validate build

# Full automation
python auto-build.py          # Full pipeline
python auto-build.py --bump  # Full + version bump
python auto-build.py --test-only  # Tests only
```

---

## File Inventory

| File | Purpose |
|------|---------|
| `build.bat` | Build Windows EXE |
| `auto-build.py` | Full automation pipeline |
| `validate.py` | API validation |
| `tests/test_core.py` | 17 production tests |
| `PRODUCTION_BUILD.md` | Full documentation |

---

## Troubleshooting

### "pyinstaller: command not found"
```powershell
pip install pyinstaller
```

### "ModuleNotFoundError: No module named 'flask'"
```powershell
pip install flask flask-cors requests
```

### Tests failing
```powershell
cd C:\Projects\x-knowledge-graph
git pull
pip install -r requirements.txt
pytest tests/ -v
```

### EXE won't start
```powershell
# Run from command line to see errors
cd C:\Projects\x-knowledge-graph\dist
XKnowledgeGraph.exe
```

---

## Automation Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SCHEDULED TASK (Daily)                         │
│                                                                      │
│  1. git pull origin main                                            │
│  2. pip install -r requirements.txt                                  │
│  3. pytest tests/ -v               ← Must pass (17 tests)           │
│  4. python validate.py              ← Must pass (8 tests)            │
│  5. build.bat                      ← Creates EXE                    │
│  6. Test EXE functionality          ← Manual verification           │
│  7. Upload to GitHub Releases       ← Optional                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. ✅ Clone repo
2. ⬜ Install dependencies
3. ⬜ Run tests
4. ⬜ Build EXE
5. ⬜ Validate build
6. ⬜ Setup scheduled task (optional)

**Ready to start?** Run Step 1 commands above.
