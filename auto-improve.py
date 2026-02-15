#!/usr/bin/env python3
"""
X Knowledge Graph - Autonomous Improvement & Distribution System
Detects failures → Analyzes → Fixes → Creates Distribution on Success

Usage:
    python auto-improve.py              # Run full pipeline
    python auto-improve.py --test-only  # Tests only
    python auto-improve.py --dist-only  # Create distribution only
"""

import subprocess
import json
import os
import sys
import re
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

# Configuration
REPO_DIR = Path(__file__).parent
DIST_DIR = REPO_DIR / "distributions"
DISTRIBUTION_DIR = DIST_DIR / f"x-knowledge-graph-v0.4.33"
GITHUB_TOKEN = os.environ.get("GITHUB_GIST_TOKEN", "")

class colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'


def log(msg, color=BLUE):
    print(f"{color}{msg}{END}")


def log_step(msg, status=""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status:
        status_color = GREEN if status == "✓" else RED
        print(f"[{timestamp}] {status_color}{status}{END} {msg}")
    else:
        print(f"[{timestamp}] {msg}")


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


def git_pull():
    """Pull latest from GitHub"""
    log_step("Pulling latest code...", "...")
    success, _ = run_command("git pull origin main")
    if success:
        log_step("Pulling latest code...", "✓")
    return success


def run_graph_validation():
    """Run comprehensive graph validation"""
    log_step("Running graph validation...", "...")
    
    # Run pytest graph tests
    success, output = run_command(
        "python -m pytest tests/test_graph_validation.py -v --tb=short"
    )
    
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
        log_step(f"Graph validation: {passed} passed, {failed} failed", "✗")
        return False, output
    
    log_step(f"Graph validation: {passed} passed", "✓")
    return True, output


def run_core_tests():
    """Run core functionality tests"""
    log_step("Running core tests...", "...")
    
    success, output = run_command(
        "python -m pytest tests/test_core.py -v --tb=short"
    )
    
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
        log_step(f"Core tests: {passed} passed, {failed} failed", "✗")
        return False, output
    
    log_step(f"Core tests: {passed} passed", "✓")
    return True, output


def run_full_validation():
    """Run full validation suite"""
    log_step("Running full validation...", "...")
    
    success, output = run_command("python validate.py")
    
    if "Failed: 0" in output or "failed: 0" in output:
        log_step("Full validation passed", "✓")
        return True, output
    
    log_step("Full validation failed", "✗")
    return False, output


def create_distribution():
    """Create distribution package"""
    log_step("Creating distribution...", "...")
    
    # Clean previous distribution
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create version directory
    version_dir = DIST_DIR / f"x-knowledge-graph-v0.4.33"
    if version_dir.exists():
        shutil.rmtree(version_dir)
    version_dir.mkdir()
    
    files_to_copy = [
        "main.py",
        "core/",
        "frontend/",
        "VERSION.txt",
        "requirements.txt",
        "build.bat",
        "build.ps1",
        "validate.py",
        "auto-build.py",
        "README.md",
        "EXPORT_FORMATS.md",
        "LAUNCH-READY.md",
    ]
    
    log_step("Copying files...", "...")
    
    for item in files_to_copy:
        src = REPO_DIR / item
        dst = version_dir / item
        
        if src.is_file():
            shutil.copy2(src, dst)
            log(f"  Copied: {item}")
        elif src.is_dir():
            shutil.copytree(src, dst)
            log(f"  Copied: {item}/")
    
    # Create distribution tar
    log_step("Creating tar archive...", "...")
    
    import tarfile
    
    tar_path = DIST_DIR / f"x-knowledge-graph-v0.4.33.tar"
    with tarfile.open(tar_path, "w") as tar:
        tar.add(version_dir, arcname=f"x-knowledge-graph-v0.4.33")
    
    # Generate checksums
    log_step("Generating checksums...", "...")
    
    checksum_file = DIST_DIR / "checksums.txt"
    with open(checksum_file, 'w') as f:
        for item in version_dir.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(DIST_DIR)
                sha256 = hashlib.sha256(item.read_bytes()).hexdigest()
                f.write(f"{sha256}  {rel_path}\n")
                log(f"  {rel_path}: {sha256[:16]}...")
    
    # Distribution summary
    size_mb = tar_path.stat().st_size / 1024 / 1024
    
    log_step("Distribution created!", "✓")
    log(f"  Location: {tar_path}")
    log(f"  Size: {size_mb:.2f} MB")
    log(f"  Checksums: {checksum_file}")
    
    return True


def git_commit_distribution():
    """Commit distribution changes"""
    log_step("Committing distribution...", "...")
    
    run_command('git add -A')
    run_command('git commit -m "Distribution v0.4.33 - ' + 
                datetime.now().strftime("%Y-%m-%d") + '"')
    
    log_step("Distribution committed", "✓")


def full_pipeline():
    """Run full improvement pipeline"""
    
    print()
    log("=" * 70, CYAN)
    log("  X KNOWLEDGE GRAPH - AUTONOMOUS IMPROVEMENT & DISTRIBUTION", CYAN)
    log("=" * 70, CYAN)
    print()
    
    results = {}
    
    # Step 1: Pull
    log_step("Pulling latest code...", "...")
    results["pull"] = git_pull()
    if not results["pull"]:
        log_step("Pipeline aborted - pull failed", "✗")
        return False
    
    # Step 2: Graph Validation
    log_step("=" * 50)
    log_step("STEP 1: Graph Population Validation")
    log_step("=" * 50)
    results["graph_validation"] = run_graph_validation()
    
    # Step 3: Core Tests
    log_step("=" * 50)
    log_step("STEP 2: Core Functionality Tests")
    log_step("=" * 50)
    results["core_tests"] = run_core_tests()
    
    # Step 4: Full Validation
    log_step("=" * 50)
    log_step("STEP 3: Full API Validation")
    log_step("=" * 50)
    results["full_validation"] = run_full_validation()
    
    # Check if all tests passed
    all_passed = all(results.values())
    
    # Step 5: Create Distribution (only if all tests pass)
    if all_passed:
        log_step("=" * 50)
        log_step("ALL TESTS PASSED - Creating Distribution")
        log_step("=" * 50)
        results["distribution"] = create_distribution()
        results["git_commit"] = git_commit_distribution()
    else:
        log_step("Tests failed - skipping distribution", "✗")
        results["distribution"] = False
        results["git_commit"] = False
    
    # Summary
    print()
    log("=" * 70, CYAN)
    log("  PIPELINE RESULTS", CYAN)
    log("=" * 70, CYAN)
    
    for step, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        color = GREEN if passed else RED
        log(f"  {step:20} {status}", color)
    
    print()
    if all_passed and results.get("distribution"):
        log("PIPELINE COMPLETE - Distribution created!", GREEN)
        log(f"  Distribution: {DIST_DIR / 'x-knowledge-graph-v0.4.33.tar'}", GREEN)
    else:
        log("PIPELINE COMPLETE WITH FAILURES", RED)
        failed_steps = [k for k, v in results.items() if not v]
        log(f"  Failed: {', '.join(failed_steps)}", RED)
    
    return all_passed


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="X Knowledge Graph Auto-Improve")
    parser.add_argument("--test-only", action="store_true", help="Tests only")
    parser.add_argument("--dist-only", action="store_true", help="Distribution only")
    
    args = parser.parse_args()
    
    if args.test_only:
        success = run_graph_validation() and run_core_tests()
    elif args.dist_only:
        success = create_distribution()
    else:
        success = full_pipeline()
    
    sys.exit(0 if success else 1)
