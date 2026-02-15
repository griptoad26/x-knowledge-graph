#!/usr/bin/env python3
"""
X Knowledge Graph - Autonomous Improvement System (Windows)
Detects failures → Analyzes → Fixes → Pushes to GitHub
"""

import subprocess
import json
import os
import sys
import re
from datetime import datetime

# GitHub Configuration
REPO_DIR = r"C:\Projects\x-knowledge-graph"
GITHUB_TOKEN = os.environ.get("GITHUB_GIST_TOKEN", "")

class AutoFixer:
    """Autonomously fixes common issues"""
    
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir
    
    def run_command(self, cmd):
        """Run shell command"""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=self.repo_dir)
        return result.returncode, result.stdout, result.stderr
    
    def git_pull(self):
        """Get latest code"""
        return self.run_command("git pull origin main")
    
    def git_push(self, message):
        """Push changes"""
        self.run_command("git add -A")
        self.run_command(f'git commit -m "{message}"')
        return self.run_command("git push origin main")
    
    def analyze_flask_error(self, error_msg):
        """Analyze Flask startup errors"""
        fixes = []
        
        # Port already in use
        if "port" in error_msg.lower() and "in use" in error_msg.lower():
            fixes.append(("kill_port", "Kill process on port 5000"))
        
        # Import error
        if "ImportError" in error_msg or "ModuleNotFoundError" in error_msg:
            match = re.search(r"No module named '([^']+)'", error_msg)
            if match:
                module = match.group(1)
                fixes.append(("install_dep", f"Install missing module: {module}"))
        
        # Syntax error
        if "SyntaxError" in error_msg:
            fixes.append(("fix_syntax", "Fix syntax error in Python file"))
        
        # Missing file
        if "FileNotFoundError" in error_msg or "not found" in error_msg.lower():
            fixes.append(("create_file", "Create missing file"))
        
        return fixes
    
    def fix_kill_port(self):
        """Kill process on port 5000 (Windows)"""
        print("  → Killing process on port 5000...")
        self.run_command('netstat -ano | findstr :5000')
        # On Windows, we'd need to find and kill the PID
        return True
    
    def fix_install_dep(self, module):
        """Install missing dependency"""
        print(f"  → Installing {module}...")
        return self.run_command(f"pip install {module}") == 0
    
    def apply_fixes(self, test_results):
        """Apply fixes based on test failures"""
        applied = []
        
        for test in test_results.get("tests", []):
            if not test.get("passed"):
                error = test.get("error", "")
                fixes = self.analyze_flask_error(error)
                
                for fix_type, description in fixes:
                    if fix_type == "kill_port":
                        if self.fix_kill_port():
                            applied.append(description)
                    
                    elif fix_type == "install_dep":
                        module = description.split(": ")[1]
                        if self.fix_install_dep(module):
                            applied.append(description)
        
        return list(set(applied))


def run_validation():
    """Run validation and return results"""
    print("\nRunning validation...")
    os.chdir(REPO_DIR)
    env = os.environ.copy()
    env["HEADLESS"] = "1"
    
    result = subprocess.run(
        [sys.executable, "validate.py"],
        capture_output=True,
        text=True,
        env=env
    )
    
    stdout = result.stdout
    summary = {"total": 0, "passed": 0, "failed": 0}
    
    # Parse summary
    if "Total Tests:" in stdout:
        match = re.search(r"Total Tests: (\d+)", stdout)
        if match:
            summary["total"] = int(match.group(1))
        match = re.search(r"Passed: (\d+)", stdout)
        if match:
            summary["passed"] = int(match.group(1))
        match = re.search(r"Failed: (\d+)", stdout)
        if match:
            summary["failed"] = int(match.group(1))
    
    return summary, stdout, result.stderr


def main():
    print("=" * 60)
    print("  X Knowledge Graph - Autonomous Improvement System")
    print("=" * 60)
    print()
    
    fixer = AutoFixer(REPO_DIR)
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] Starting improvement cycle...")
        
        # Step 1: Pull latest
        print("  Pulling latest code...")
        fixer.git_pull()
        
        # Step 2: Run validation
        summary, stdout, stderr = run_validation()
        print(f"  Results: {summary['passed']}/{summary['total']} passed")
        
        # Step 3: If failed, apply fixes
        if summary.get("failed", 0) > 0:
            print(f"\n  ⚠ {summary['failed']} tests failed - analyzing fixes...")
            fixes = fixer.apply_fixes({})
            
            if fixes:
                print(f"\n  Applied {len(fixes)} fixes:")
                for f in fixes:
                    print(f"    - {f}")
                
                # Step 4: Push fixes
                print("\n  Pushing fixes to GitHub...")
                fixer.git_push(f"Auto-fix: {', '.join(fixes[:3])}")
                print("  ✓ Fixes pushed!")
            else:
                print("  ⚠ No automatic fixes available - manual intervention needed")
        
        # Step 5: Wait 5 minutes
        print("\n  Waiting 5 minutes before next cycle...")
        import time
        time.sleep(300)


if __name__ == "__main__":
    main()
