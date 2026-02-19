#!/bin/bash
# VPS Health Monitor - Checks server every 5 minutes
LOG_FILE="/home/molty/.openclaw/workspace/projects/x-knowledge-graph/logs/vps-health.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if server responds
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://66.179.191.93:51338 2>/dev/null)

if [ "$RESPONSE" = "200" ]; then
    log "OK - Server responding (HTTP $RESPONSE)"
    exit 0
else
    log "ERROR - Server not responding (HTTP $RESPONSE)"
    
    # Try to restart
    ssh -o StrictHostKeyChecking=no Administrator@66.179.191.93 "cd C:\Projects\x-knowledge-graph && python main.py --port 51338 &" 2>/dev/null
    
    sleep 5
    
    # Check again
    RESPONSE2=$(curl -s -o /dev/null -w "%{http_code}" http://66.179.191.93:51338 2>/dev/null)
    if [ "$RESPONSE2" = "200" ]; then
        log "OK - Server restarted successfully"
    else
        log "ERROR - Server restart failed"
    fi
    exit 1
fi
