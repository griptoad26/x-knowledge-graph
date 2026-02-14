#!/usr/bin/env python3
"""
X Knowledge Graph - Automated Validation Script
Tests all API endpoints and reports results
"""

import sys
import os
import json
import time
import requests
import subprocess
import signal
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:PORT"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(APP_DIR, "test_data")
REPORT_FILE = os.path.join(APP_DIR, "validation_report.json")

class colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_result(test_name, passed, message=""):
    status = f"{colors.GREEN}PASS{colors.END}" if passed else f"{colors.RED}FAIL{colors.END}"
    print(f"  [{status}] {test_name}")
    if message:
        print(f"         {message}")
    return passed

def run_validation():
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {"total": 0, "passed": 0, "failed": 0}
    }
    
    # Start Flask app
    print(f"\n{colors.BLUE}Starting X Knowledge Graph application...{colors.END}\n")
    
    port = 5000
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=APP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONUNBUFFERED": "1"}
    )
    
    # Wait for app to start
    time.sleep(3)
    
    base_url = f"http://localhost:{port}"
    
    # Test 1: Health Check
    print(f"{colors.BLUE}Running API Tests...{colors.END}\n")
    
    try:
        r = requests.get(f"{base_url}/api/health", timeout=10)
        passed = r.status_code == 200 and r.json().get("status") == "ok"
        results["tests"].append({
            "name": "Health Check",
            "passed": passed,
            "response": r.json() if passed else r.text
        })
        print_result("Health Check", passed, r.json().get("version", ""))
    except Exception as e:
        results["tests"].append({"name": "Health Check", "passed": False, "error": str(e)})
        print_result("Health Check", False, str(e))
    
    # Test 2: Parse X Export
    x_path = os.path.join(TEST_DATA_DIR, "x_export")
    if os.path.exists(x_path):
        try:
            r = requests.post(f"{base_url}/api/parse-export", 
                           json={"x_path": x_path, "export_type": "x", "graph_mode": "all"},
                           timeout=30)
            data = r.json()
            passed = r.status_code == 200 and "stats" in data
            results["tests"].append({
                "name": "Parse X Export",
                "passed": passed,
                "stats": data.get("stats", {}) if passed else {}
            })
            stats = data.get("stats", {})
            print_result("Parse X Export", passed, 
                        f"Tweets: {stats.get('total_tweets', 0)}, Actions: {stats.get('total_actions', 0)}")
        except Exception as e:
            results["tests"].append({"name": "Parse X Export", "passed": False, "error": str(e)})
            print_result("Parse X Export", False, str(e))
    else:
        print_result("Parse X Export", False, f"Test data not found: {x_path}")
    
    # Test 3: Parse Grok Export
    grok_path = os.path.join(TEST_DATA_DIR, "grok_export")
    if os.path.exists(grok_path):
        try:
            r = requests.post(f"{base_url}/api/parse-export",
                           json={"grok_path": grok_path, "export_type": "grok", "graph_mode": "all"},
                           timeout=30)
            data = r.json()
            passed = r.status_code == 200 and "stats" in data
            results["tests"].append({
                "name": "Parse Grok Export",
                "passed": passed,
                "stats": data.get("stats", {}) if passed else {}
            })
            stats = data.get("stats", {})
            print_result("Parse Grok Export", passed,
                        f"Posts: {stats.get('total_tweets', 0)}, Actions: {stats.get('total_actions', 0)}")
        except Exception as e:
            results["tests"].append({"name": "Parse Grok Export", "passed": False, "error": str(e)})
            print_result("Parse Grok Export", False, str(e))
    else:
        print_result("Parse Grok Export", False, f"Test data not found: {grok_path}")
    
    # Test 4: Get Graph
    try:
        r = requests.get(f"{base_url}/api/graph", timeout=10)
        data = r.json()
        passed = r.status_code == 200 and "nodes" in data
        results["tests"].append({
            "name": "Get Graph",
            "passed": passed,
            "nodes": len(data.get("nodes", [])),
            "edges": len(data.get("edges", []))
        })
        print_result("Get Graph", passed, f"Nodes: {len(data.get('nodes', []))}, Edges: {len(data.get('edges', []))}")
    except Exception as e:
        results["tests"].append({"name": "Get Graph", "passed": False, "error": str(e)})
        print_result("Get Graph", False, str(e))
    
    # Test 5: Get Actions
    try:
        r = requests.get(f"{base_url}/api/actions", timeout=10)
        data = r.json()
        passed = r.status_code == 200
        results["tests"].append({
            "name": "Get Actions",
            "passed": passed,
            "count": len(data) if isinstance(data, list) else 0
        })
        print_result("Get Actions", passed, f"Count: {len(data) if isinstance(data, list) else 0}")
    except Exception as e:
        results["tests"].append({"name": "Get Actions", "passed": False, "error": str(e)})
        print_result("Get Actions", False, str(e))
    
    # Test 6: Get Topics
    try:
        r = requests.get(f"{base_url}/api/topics", timeout=10)
        data = r.json()
        passed = r.status_code == 200
        results["tests"].append({
            "name": "Get Topics",
            "passed": passed,
            "count": len(data) if isinstance(data, dict) else 0
        })
        print_result("Get Topics", passed, f"Count: {len(data) if isinstance(data, dict) else 0}")
    except Exception as e:
        results["tests"].append({"name": "Get Topics", "passed": False, "error": str(e)})
        print_result("Get Topics", False, str(e))
    
    # Test 7: Get Flows
    try:
        r = requests.get(f"{base_url}/api/flows", timeout=10)
        data = r.json()
        passed = r.status_code == 200
        results["tests"].append({
            "name": "Get Flows",
            "passed": passed,
            "flows": data
        })
        print_result("Get Flows", passed)
    except Exception as e:
        results["tests"].append({"name": "Get Flows", "passed": False, "error": str(e)})
        print_result("Get Flows", False, str(e))
    
    # Test 8: Todoist Export (mock)
    try:
        r = requests.post(f"{base_url}/api/export-todoist", json={}, timeout=10)
        # Should fail gracefully without API token
        passed = r.status_code in [200, 400]  # 400 = no token (expected)
        results["tests"].append({
            "name": "Todoist Export",
            "passed": passed,
            "status_code": r.status_code
        })
        print_result("Todoist Export", passed, f"Status: {r.status_code}")
    except Exception as e:
        results["tests"].append({"name": "Todoist Export", "passed": False, "error": str(e)})
        print_result("Todoist Export", False, str(e))
    
    # Cleanup - stop the Flask app
    print(f"\n{colors.BLUE}Stopping application...{colors.END}\n")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    
    # Summary
    results["summary"]["total"] = len(results["tests"])
    results["summary"]["passed"] = sum(1 for t in results["tests"] if t.get("passed"))
    results["summary"]["failed"] = results["summary"]["total"] - results["summary"]["passed"]
    
    print(f"\n{colors.BLUE}=== VALIDATION SUMMARY ==={colors.END}\n")
    print(f"  Total Tests: {results['summary']['total']}")
    print(f"  {colors.GREEN}Passed: {results['summary']['passed']}{colors.END}")
    print(f"  {colors.RED}Failed: {results['summary']['failed']}{colors.END}")
    
    # Save report
    with open(REPORT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n{colors.BLUE}Report saved to: {REPORT_FILE}{colors.END}\n")
    
    return results["summary"]["failed"] == 0

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
