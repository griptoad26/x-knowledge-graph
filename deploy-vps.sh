#!/bin/bash
# X Knowledge Graph - VPS Auto-Deploy Script
# Usage: Run via SSH on VPS or from local via ssh command
# Note: Set GIT_REPO_TOKEN environment variable or configure git credential helper

VPS_USER="administrator"
VPS_HOST="66.179.191.93"
VPS_PATH="/projects/x-knowledge-graph"
GIT_REPO="https://github.com/griptoad26/x-knowledge-graph.git"

echo "========================================"
echo "  X Knowledge Graph - VPS Auto-Deploy"
echo "========================================"
echo ""

# Stop existing app
echo "[1/6] Stopping existing app..."
ssh $VPS_USER@$VPS_HOST "pkill -f 'python main.py' 2>/dev/null; sleep 1"

# Backup current version
echo "[2/6] Backing up current version..."
ssh $VPS_USER@$VPS_HOST "cd /projects && mv x-knowledge-graph x-knowledge-graph-backup-\$(date +%Y%m%d-%H%M%S) 2>/dev/null"

# Pull latest from git
echo "[3/6] Pulling latest from git..."
ssh $VPS_USER@$VPS_HOST "cd /projects && git clone $GIT_REPO x-knowledge-graph-new 2>/dev/null || (cd x-knowledge-graph-new && git pull)"
ssh $VPS_USER@$VPS_HOST "mv x-knowledge-graph-new x-knowledge-graph"

# Install dependencies if needed
echo "[4/6] Installing dependencies..."
ssh $VPS_USER@$VPS_HOST "cd $VPS_PATH && pip install -q -r requirements.txt 2>/dev/null"

# Start application
echo "[5/6] Starting application..."
ssh $VPS_USER@$VPS_HOST "cd $VPS_PATH && nohup python main.py > app.log 2>&1 &"
ssh $VPS_USER@$VPS_HOST "sleep 3"

# Verify
echo "[6/6] Verifying deployment..."
ssh $VPS_USER@$VPS_HOST "curl -s http://localhost:51338/health"

echo ""
echo "========================================"
echo "  Deployment Complete"
echo "========================================"
echo ""
echo "App running at: http://$VPS_HOST:51338"
echo "SSH access: ssh $VPS_USER@$VPS_HOST"
