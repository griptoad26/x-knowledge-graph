#!/usr/bin/env python3
"""
X Knowledge Graph - Automated Test Scheduler
Sets up cron job or Windows Scheduled Task for daily test runs

Usage:
    python setup_scheduler.py --install    # Install scheduled task
    python setup_scheduler.py --remove     # Remove scheduled task
    python setup_scheduler.py --status     # Check status
    python setup_scheduler.py --run        # Run tests immediately
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
import subprocess

# Configuration
PROJECT_ROOT = Path(__file__).parent
SCRIPT_DIR = PROJECT_ROOT
TEST_SCRIPT = PROJECT_ROOT / "test_all_views.py"
RESULTS_DIR = PROJECT_ROOT / "test_results"
CRON_SCRIPT = PROJECT_ROOT / "run-tests-cron.sh"
WINDOWS_SCRIPT = PROJECT_ROOT / "run-full-tests.ps1"

# Default paths
WINDOWS_TASK_NAME = "XKG Daily Test"
CRON_ID = "xkg-daily-test"


def detect_platform():
    """Detect operating system"""
    if sys.platform.startswith('win'):
        return 'windows'
    elif sys.platform.startswith('linux'):
        # Check if WSL
        if os.path.exists('/mnt/c/Users'):
            return 'wsl'
        return 'linux'
    elif sys.platform.startswith('darwin'):
        return 'macos'
    return 'unknown'


def setup_windows_task():
    """Set up Windows Scheduled Task"""
    print("Setting up Windows Scheduled Task...")
    
    if not os.path.exists(WINDOWS_SCRIPT):
        print(f"Error: PowerShell script not found: {WINDOWS_SCRIPT}")
        return False
    
    # Create task using schtasks
    task_command = f'schtasks /create /tn "{WINDOWS_TASK_NAME}" /tr "powershell -ExecutionPolicy Bypass -File \\"{WINDOWS_SCRIPT}\\"" /sc daily /st 09:00 /ri 60 /du 1440 /f'
    
    try:
        result = subprocess.run(task_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Task '{WINDOWS_TASK_NAME}' created successfully")
            print("  Schedule: Daily at 9:00 AM, repeats every 60 minutes")
            return True
        else:
            print(f"Error creating task: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def setup_wsl_cron():
    """Set up cron job via WSL"""
    print("Setting up WSL cron job...")
    
    # Create cron script
    cron_content = f'''#!/bin/bash
# X Knowledge Graph - Daily Test Runner
# Runs via cron in WSL

cd "{PROJECT_ROOT}"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests
python3 "{TEST_SCRIPT}" --html

# Upload to Gist if token available
if [ -n "$GITHUB_GIST_TOKEN" ]; then
    python3 "{TEST_SCRIPT}" --gist
fi

# Send notification (Windows)
if command -v powershell.exe &> /dev/null; then
    powershell.exe -Command 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show("XKG Tests Completed", "Test Results")'
fi
'''

    CRON_SCRIPT.write_text(cron_content)
    CRON_SCRIPT.chmod(0o755)
    
    # Add to crontab
    cron_entry = f"0 9 * * * {CRON_SCRIPT} >> {PROJECT_ROOT}/cron.log 2>&1"
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        
        # Check if entry already exists
        if CRON_ID not in current_cron:
            # Add new entry
            new_cron = current_cron + f"\n{cron_entry}\n"
            subprocess.run(['crontab', '-'], input=new_cron, capture_output=True)
        
        print("✓ Cron job configured")
        print("  Schedule: Daily at 9:00 AM")
        print(f"  Script: {CRON_SCRIPT}")
        return True
        
    except Exception as e:
        print(f"Error setting up cron: {e}")
        return False


def setup_linux_cron():
    """Set up native Linux cron"""
    print("Setting up Linux cron job...")
    
    # Create systemd timer unit instead
    timer_content = '''[Unit]
Description=X Knowledge Graph Daily Test Runner

[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
'''

    service_content = f'''[Unit]
Description=X Knowledge Graph Daily Test Runner

[Service]
Type=oneshot
WorkingDirectory={PROJECT_ROOT}
ExecStart={sys.executable} {TEST_SCRIPT} --html
User=molty

[Install]
WantedBy=multi-user.target
'''

    timer_file = Path("/etc/systemd/system/xkg-daily-test.timer")
    service_file = Path("/etc/systemd/system/xkg-daily-test.service")

    try:
        # Only if running as root
        if os.geteuid() == 0:
            timer_file.write_text(timer_content)
            service_file.write_text(service_content)
            subprocess.run(['systemctl', 'daemon-reload'])
            subprocess.run(['systemctl', 'enable', 'xkg-daily-test.timer'])
            subprocess.run(['systemctl', 'start', 'xkg-daily-test.timer'])
            print("✓ Systemd timer configured")
        else:
            print("Note: Run as root to install systemd timer")
            print(f"Timer file: {timer_file}")
            print(f"Service file: {service_file}")
        return True
    except Exception as e:
        print(f"Error setting up systemd timer: {e}")
        return False


def remove_windows_task():
    """Remove Windows Scheduled Task"""
    print(f"Removing Windows task: {WINDOWS_TASK_NAME}")
    
    try:
        result = subprocess.run(
            f'schtasks /delete /tn "{WINDOWS_TASK_NAME}" /f',
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✓ Task removed")
            return True
        else:
            print(f"Note: {result.stderr}")
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def remove_cron():
    """Remove cron job"""
    print("Removing cron job...")
    
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        
        # Remove our entry
        lines = [l for l in current_cron.split('\n') if CRON_ID not in l and 'xkg-daily-test' not in l]
        new_cron = '\n'.join(lines)
        
        subprocess.run(['crontab', '-'], input=new_cron, capture_output=True)
        
        # Remove cron script
        if CRON_SCRIPT.exists():
            CRON_SCRIPT.unlink()
        
        print("✓ Cron job removed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def check_status():
    """Check scheduler status"""
    platform = detect_platform()
    print(f"Platform: {platform}")
    print()
    
    if platform == 'windows':
        try:
            result = subprocess.run(
                f'schtasks /query /tn "{WINDOWS_TASK_NAME}"',
                shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"✓ Task '{WINDOWS_TASK_NAME}' exists")
                # Parse task info
                for line in result.stdout.split('\n'):
                    if 'Last Run' in line or 'Next Run' in line:
                        print(f"  {line.strip()}")
            else:
                print(f"✗ Task '{WINDOWS_TASK_NAME}' not found")
        except Exception as e:
            print(f"Error: {e}")
    
    elif platform in ['linux', 'wsl']:
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0 and CRON_ID in result.stdout:
                print("✓ Cron job configured")
                for line in result.stdout.split('\n'):
                    if CRON_ID in line:
                        print(f"  {line.strip()}")
            else:
                print("✗ Cron job not configured")
        except Exception as e:
            print(f"Error: {e}")
    
    # Check results directory
    if RESULTS_DIR.exists():
        results = list(RESULTS_DIR.glob("*.json"))
        print(f"\n✓ Results directory: {len(results)} result files")
    else:
        print("\n✗ No results directory found")


def run_tests_now():
    """Run tests immediately"""
    print("Running tests immediately...")
    
    if os.path.exists(WINDOWS_SCRIPT) and detect_platform() == 'windows':
        try:
            subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', WINDOWS_SCRIPT])
        except Exception as e:
            print(f"Error: {e}")
    else:
        cmd = [sys.executable, str(TEST_SCRIPT)]
        if os.path.exists(TEST_SCRIPT):
            subprocess.run(cmd)
        else:
            print(f"Test script not found: {TEST_SCRIPT}")


def main():
    parser = argparse.ArgumentParser(description="X Knowledge Graph - Test Scheduler")
    parser.add_argument("--install", action="store_true", help="Install scheduled task")
    parser.add_argument("--remove", action="store_true", help="Remove scheduled task")
    parser.add_argument("--status", action="store_true", help="Check scheduler status")
    parser.add_argument("--run", action="store_true", help="Run tests immediately")
    
    args = parser.parse_args()
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(exist_ok=True)
    
    platform = detect_platform()
    print(f"Detected platform: {platform}")
    
    if args.install:
        if platform == 'windows':
            setup_windows_task()
        elif platform == 'wsl':
            setup_wsl_cron()
        elif platform == 'linux':
            setup_linux_cron()
        else:
            print("Unsupported platform for scheduled tasks")
    
    elif args.remove:
        if platform == 'windows':
            remove_windows_task()
        else:
            remove_cron()
    
    elif args.status:
        check_status()
    
    elif args.run:
        run_tests_now()
    
    else:
        # Default: show help
        print("X Knowledge Graph - Automated Test Scheduler")
        print()
        print("Usage:")
        print("  --install   Set up daily scheduled tests")
        print("  --remove    Remove scheduled tests")
        print("  --status    Check scheduler status")
        print("  --run       Run tests immediately")
        print()
        print(f"Platform: {platform}")
        
        if platform == 'windows':
            print(f"\nPowerShell script: {WINDOWS_SCRIPT}")
            print("Install command: python setup_scheduler.py --install")
        else:
            print(f"\nTest script: {TEST_SCRIPT}")
            print("Install command: python setup_scheduler.py --install")


if __name__ == "__main__":
    main()
