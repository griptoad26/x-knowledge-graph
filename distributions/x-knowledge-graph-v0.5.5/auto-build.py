#!/usr/bin/env python3
"""
X Knowledge Graph - Automated Build & Validation Pipeline
Fully automated: Pull → Test → Build → Validate → Release

Usage:
    python auto-build.py                    # Full pipeline
    python auto-build.py --test-only       # Test only
    python auto-build.py --build-only      # Build only
    python auto-build.py --release         # Full release
"""

import subprocess
import sys
import os
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path

# Configuration
REPO_DIR = Path(__file__).parent
VERSION_FILE = REPO_DIR / "VERSION.txt"
DIST_DIR = REPO_DIR / "dist"
BUILD_DIR = REPO_DIR / "build"
APP_NAME = "XKnowledgeGraph"

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
END = '\033[0m'


def log(msg, color=BLUE):
    print(f"{color}{msg}{END}")


def log_step(step, status=""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status:
        status_color = GREEN if status == "✓" else RED
        print(f"[{timestamp}] {status_color}{status}{END} {step}")
    else:
        print(f"[{timestamp}] {step}")


def run_command(cmd, cwd=None, check=True):
    """Run shell command"""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd or REPO_DIR,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        log(f"Command failed: {cmd}", RED)
        log(f"Error: {result.stderr}", RED)
        return False, result.stderr
    return True, result.stdout


def get_version():
    """Read current version"""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "0.0.0"


def bump_version(bumptype="patch"):
    """Bump version number"""
    version = get_version()
    parts = version.split('.')
    
    if bumphype == "major":
        parts[0] = str(int(parts[0]) + 1)
        parts[1] = "0"
        parts[2] = "0"
    elif bumphype == "minor":
        parts[1] = str(int(parts[1]) + 1)
        parts[2] = "0"
    else:  # patch
        parts[2] = str(int(parts[2]) + 1)
    
    new_version = '.'.join(parts)
    VERSION_FILE.write_text(new_version + '\n')
    
    # Update main.py version
    main_py = REPO_DIR / "main.py"
    content = main_py.read_text()
    content = content.replace(f'v{version}', f'v{new_version}')
    main_py.write_text(content)
    
    return new_version


def git_pull():
    """Pull latest from GitHub"""
    log_step("Pulling latest code...", "...")
    success, _ = run_command("git pull origin main")
    if success:
        log_step("Pulling latest code...", "✓")
    else:
        log_step("Pulling latest code...", "✗")
    return success


def run_tests():
    """Run pytest test suite"""
    log_step("Running tests...", "...")
    
    # First, run core tests
    success, output = run_command("python -m pytest tests/test_core.py -v --tb=short")
    
    # Parse results
    passed = 0
    failed = 0
    
    if "passed" in output:
        import re
        match = re.search(r'(\d+) passed', output)
        if match:
            passed = int(match.group(1))
        match = re.search(r'(\d+) failed', output)
        if match:
            failed = int(match.group(1))
    
    if failed > 0:
        log_step(f"Tests: {passed} passed, {failed} failed", "✗")
        return False
    
    log_step(f"Tests: {passed} passed, {failed} failed", "✓")
    return True


def run_validation():
    """Run validation script"""
    log_step("Running validation...", "...")
    success, output = run_command("python validate.py")
    
    if "Failed: 0" in output or "8 passed" in output:
        log_step("Validation passed", "✓")
        return True
    
    log_step("Validation failed", "✗")
    return False


def build_windows():
    """Build Windows EXE"""
    log_step("Building Windows EXE...", "...")
    
    # Clean previous builds
    if BUILD_DIR.exists():
        run_command(f"rmdir /s /q \"{BUILD_DIR}\"")
    if DIST_DIR.exists():
        run_command(f"rmdir /s /q \"{DIST_DIR}\"")
    
    # Run PyInstaller
    cmd = f'''
    pyinstaller --onefile ^
        --name {APP_NAME} ^
        --windowed ^
        --clean ^
        --noconsole ^
        --add-data "frontend;frontend" ^
        --add-data "core;core" ^
        --hidden-import flask ^
        --hidden-import flask_cors ^
        --hidden-import requests ^
        main.py
    '''
    
    success, output = run_command(cmd)
    
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / 1024 / 1024
        log_step(f"EXE built: {exe_path.name} ({size_mb:.2f} MB)", "✓")
        
        # Generate checksum
        sha256 = hashlib.sha256(exe_path.read_bytes()).hexdigest()
        checksum_file = DIST_DIR / "checksum.txt"
        checksum_file.write_text(f"{sha256} {APP_NAME}.exe\n")
        log_step(f"Checksum: {sha256[:16]}...", "✓")
        
        return True
    
    log_step("Build failed - EXE not found", "✗")
    return False


def test_exe():
    """Test the built EXE"""
    log_step("Testing built EXE...", "...")
    
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    
    if not exe_path.exists():
        log_step("EXE not found", "✗")
        return False
    
    # Run basic functionality test
    success, _ = run_command(f'"{exe_path}" --help')
    
    if success:
        log_step("EXE runs successfully", "✓")
        return True
    
    log_step("EXE test failed", "✗")
    return False


def create_release_notes(version):
    """Create release notes"""
    notes = f"""# {APP_NAME} v{version}

## Release Notes

**Date:** {datetime.now().strftime('%Y-%m-%d')}

### What's New
- See CHANGELOG.md for full details

### Installation
1. Extract the zip file
2. Run {APP_NAME}.exe

### Requirements
- Windows 10+
- 100MB free space
- No Python required (self-contained)

### Verification
- SHA256 checksum provided in checksum.txt
- Verify with: `certutil -hashfile XKnowledgeGraph.exe SHA256`

### Support
- Report issues: https://github.com/griptoad26/x-knowledge-graph/issues
"""
    
    notes_file = DIST_DIR / "RELEASE_NOTES.md"
    notes_file.write_text(notes)
    log_step("Release notes created", "✓")


def git_commit_version(version):
    """Commit version bump"""
    log_step("Committing version...", "...")
    run_command(f'git commit -am "Bump version to {version}"')
    run_command(f'git tag "v{version}"')
    log_step(f"Committed and tagged v{version}", "✓")


def full_pipeline():
    """Run full build pipeline"""
    version = get_version()
    
    print()
    log("=" * 60, CYAN)
    log(f"  {APP_NAME} - Build Pipeline v{version}", CYAN)
    log("=" * 60, CYAN)
    print()
    
    results = {}
    
    # Step 1: Pull
    results["pull"] = git_pull()
    if not results["pull"]:
        log_step("Pipeline aborted - pull failed", "✗")
        return False
    
    # Step 2: Tests
    results["tests"] = run_tests()
    if not results["tests"]:
        log_step("Pipeline aborted - tests failed", "✗")
        return False
    
    # Step 3: Validation
    results["validation"] = run_validation()
    if not results["validation"]:
        log_step("Pipeline aborted - validation failed", "✗")
        return False
    
    # Step 4: Build
    results["build"] = build_windows()
    if not results["build"]:
        log_step("Pipeline aborted - build failed", "✗")
        return False
    
    # Step 5: Test EXE
    results["test_exe"] = test_exe()
    
    # Step 6: Release notes
    create_release_notes(version)
    
    # Summary
    print()
    log("=" * 60, CYAN)
    log("  Pipeline Results", CYAN)
    log("=" * 60, CYAN)
    
    all_passed = True
    for step, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        color = GREEN if passed else RED
        log(f"  {step:12} {status}", color)
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        log("Pipeline completed successfully!", GREEN)
        log(f"EXE location: {DIST_DIR / APP_NAME}.exe", GREEN)
    else:
        log("Pipeline completed with failures", RED)
    
    return all_passed


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="X Knowledge Graph Build Pipeline")
    parser.add_argument("--test-only", action="store_true", help="Run tests only")
    parser.add_argument("--build-only", action="store_true", help="Build EXE only")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], default="patch",
                       help="Version bump type")
    
    args = parser.parse_args()
    
    if args.test_only:
        success = run_tests()
    elif args.build_only:
        success = build_windows()
    else:
        if args.bump:
            new_version = bump_version(args.bump)
            log(f"Version bumped to {new_version}", GREEN)
        success = full_pipeline()
    
    sys.exit(0 if success else 1)
