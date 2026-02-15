#!/usr/bin/env python3
"""
X Knowledge Graph - Automated Validation Script
Tests all API endpoints and uploads results to GitHub Gist

Usage:
    # Set GitHub token first (once):
    $env:GITHUB_GIST_TOKEN = "your-github-token"
    
    # Run validation:
    python validate.py
"""

import sys
import os
import json
import time
import requests
import subprocess
import signal
from datetime import datetime

# GitHub Gist Configuration - Token from environment variable
GITHUB_TOKEN = os.environ.get("GITHUB_GIST_TOKEN", "")
GIST_DESCRIPTION = "X Knowledge Graph Validation Results"
GIST_FILENAME = "validation_report.json"

# Store Gist URL for polling
GIST_URL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gist_url.txt")

class colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def get_gist_url():
    if os.path.exists(GIST_URL_FILE):
        with open(GIST_URL_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_gist_url(url):
    with open(GIST_URL_FILE, 'w') as f:
        f.write(url)

def upload_to_gist(report_json):
    """Upload validation report to GitHub Gist and return URL"""
    if not GITHUB_TOKEN:
        print(f"{colors.YELLOW}GitHub token not set. Skipping Gist upload.{colors.END}")
        print(f"  Set with: $env:GITHUB_GIST_TOKEN = \"your-token\"")
        return None
    
    gist_url = get_gist_url()
    
    if gist_url:
        gist_id = gist_url.split('/')[-1]
        url = f"https://api.github.com/gists/{gist_id}"
        method = "PATCH"
    else:
        url = "https://api.github.com/gists"
        method = "POST"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    files = {
        GIST_FILENAME: json.dumps(report_json, indent=2)
    }
    
    data = {
        "description": f"{GIST_DESCRIPTION} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "public": True,
        "files": files
    }
    
    try:
        if method == "PATCH":
            response = requests.patch(url, headers=headers, json=data, timeout=30)
        else:
            response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            gist_url = result["html_url"]
            save_gist_url(gist_url)
            return gist_url
        else:
            print(f"{colors.RED}Gist upload failed: {response.status_code}{colors.END}")
            return None
    except Exception as e:
        print(f"{colors.RED}Gist upload error: {e}{colors.END}")
        return None

def print_result(test_name, passed, message=""):
    status = f"{colors.GREEN}PASS{colors.END}" if passed else f"{colors.RED}FAIL{colors.END}"
    print(f"  [{status}] {test_name}")
    if message:
        print(f"         {message}")
    return passed

def run_validation():
    results = {
        "timestamp": datetime.now().isoformat(),
        "version": "0.4.33",
        "tests": [],
        "summary": {"total": 0, "passed": 0, "failed": 0},
        "status": "running"
    }
    
    print(f"\n{colors.BLUE}Starting X Knowledge Graph validation...{colors.END}\n")
    print(f"{colors.BLUE}VPS: IONOS Windows Server{colors.END}")
    print(f"{colors.BLUE}Time: {results['timestamp']}{colors.END}\n")
    
    if not GITHUB_TOKEN:
        print(f"{colors.YELLOW}WARNING: GitHub token not set. Results will not be uploaded.{colors.END}")
        print(f"  Set token: $env:GITHUB_GIST_TOKEN = \"your-github-token-with-gist-scope\"")
        print()
    
    # Start Flask app
    print(f"{colors.BLUE}Starting Flask application...{colors.END}")
    
    app_dir = os.path.dirname(os.path.abspath(__file__))
    port = 5000
    
    # Kill any existing Flask process on port 5000
    try:
        import subprocess
        subprocess.run(["fuser", "-k", f"{port}/tcp"], stderr=subprocess.DEVNULL, timeout=5)
    except:
        pass
    
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=app_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONUNBUFFERED": "1"}
    )
    
    # Wait for app to start (up to 15 seconds)
    print("Waiting for Flask to start...")
    started = False
    for i in range(15):
        time.sleep(1)
        try:
            r = requests.get(f"http://127.0.0.1:{port}/api/health", timeout=2)
            if r.status_code == 200:
                started = True
                print(f"Flask started after {i+1} seconds")
                break
        except:
            pass
    
    if not started:
        stdout, stderr = process.communicate(timeout=5)
        print(f"{colors.RED}Flask failed to start!{colors.END}")
        print(f"stdout: {stdout.decode()[:500]}")
        print(f"stderr: {stderr.decode()[:500]}")
        results["tests"].append({"name": "Flask Startup", "passed": False, "error": stderr.decode()[:500]})
        print_result("Flask Startup", False)
        # Continue with error
    
    base_url = f"http://localhost:{port}"
    
    # Test 1: Health Check
    print(f"\n{colors.BLUE}Running API Tests...{colors.END}\n")
    
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
    test_data_dir = os.path.join(app_dir, "test_data")
    x_path = os.path.join(test_data_dir, "x_export")
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
        results["tests"].append({"name": "Parse X Export", "passed": False, "error": f"Path not found: {x_path}"})
    
    # Test 3: Parse Grok Export
    grok_path = os.path.join(test_data_dir, "grok_export")
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
        results["tests"].append({"name": "Parse Grok Export", "passed": False, "error": f"Path not found: {grok_path}"})
    
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
        results["tests"].append({"name": "Get Flows", "passed": passed})
        print_result("Get Flows", passed)
    except Exception as e:
        results["tests"].append({"name": "Get Flows", "passed": False, "error": str(e)})
        print_result("Get Flows", False, str(e))
    
    # Test 8: Todoist Export (mock)
    try:
        r = requests.post(f"{base_url}/api/export-todoist", json={}, timeout=10)
        passed = r.status_code in [200, 400]
        results["tests"].append({"name": "Todoist Export", "passed": passed, "status_code": r.status_code})
        print_result("Todoist Export", passed, f"Status: {r.status_code}")
    except Exception as e:
        results["tests"].append({"name": "Todoist Export", "passed": False, "error": str(e)})
        print_result("Todoist Export", False, str(e))
    
    # Cleanup
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
    results["status"] = "completed" if results["summary"]["failed"] == 0 else "failed"
    
    print(f"\n{colors.BLUE}=== VALIDATION SUMMARY ==={colors.END}\n")
    print(f"  Total Tests: {results['summary']['total']}")
    print(f"  {colors.GREEN}Passed: {results['summary']['passed']}{colors.END}")
    print(f"  {colors.RED}Failed: {results['summary']['failed']}{colors.END}")
    
    # Upload to Gist
    print(f"\n{colors.BLUE}Uploading results to GitHub Gist...{colors.END}")
    gist_url = upload_to_gist(results)
    if gist_url:
        print(f"\n{colors.GREEN}Results uploaded!{colors.END}")
        print(f"  Gist URL: {gist_url}")
    else:
        print(f"\n{colors.YELLOW}Skipped Gist upload (no token){colors.END}")
    
    print(f"\n{colors.BLUE}=== Validation Complete ==={colors.END}\n")
    
    return results["summary"]["failed"] == 0

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
