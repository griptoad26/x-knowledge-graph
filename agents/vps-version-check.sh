#!/bin/bash
# Version Check - Compares local vs VPS version
LOG_FILE="/home/molty/.openclaw/workspace/projects/x-knowledge-graph/logs/version-check.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

LOCAL_VERSION=$(cat /home/molty/.openclaw/workspace/projects/x-knowledge-graph/VERSION.txt 2>/dev/null)
VPS_VERSION=$(ssh -o StrictHostKeyChecking=no Administrator@66.179.191.93 "type C:\Projects\x-knowledge-graph\VERSION.txt" 2>/dev/null | tr -d '\r\n')

log "Local: $LOCAL_VERSION, VPS: $VPS_VERSION"

if [ "$LOCAL_VERSION" != "$VPS_VERSION" ]; then
    log "VERSION_MISMATCH - Local: $LOCAL_VERSION, VPS: $VPS_VERSION"
    # Trigger deploy
    cd /home/molty/.openclaw/workspace/projects/x-knowledge-graph
    python3 auto-improve.py 2>/dev/null || true
    
    # Deploy
    LATEST=$(ls -t distributions/x-knowledge-graph-v*.tar 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
        log "Deploying $LATEST..."
        scp "$LATEST" Administrator@66.179.191.93:/projects/ 2>/dev/null
        
        ssh -o StrictHostKeyChecking=no Administrator@66.179.191.93 "
            taskkill /F /IM python.exe 2>nul || true
            tar -xf /projects/x-knowledge-graph-v*.tar
            copy /Y x-knowledge-graph-v*\frontend\index.html frontend\index.html
            copy /Y x-knowledge-graph-v*\main.py .
            copy /Y x-knowledge-graph-v*\VERSION.txt .
            python main.py --port 51338 &
        " 2>/dev/null
        
        sleep 5
        
        NEW_VPS=$(ssh -o StrictHostKeyChecking=no Administrator@66.179.191.93 "curl -s http://localhost:51338 | grep -o 'v[0-9.]*'" 2>/dev/null)
        log "VPS now running: $NEW_VPS"
    fi
else
    log "OK - Versions match ($LOCAL_VERSION)"
fi
