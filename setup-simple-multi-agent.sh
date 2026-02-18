#!/bin/bash
# XKG Simple Multi-Agent Setup
# Uses built-in antfarm workflows + custom cron scripts

set -e

echo "=========================================="
echo "XKG Multi-Agent Setup (Simplified)"
echo "=========================================="

PROJECT_DIR="/home/molty/.openclaw/workspace/projects/x-knowledge-graph"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# 1. Install built-in antfarm workflows
echo ""
echo "1. Installing antfarm workflows..."
cd ~/.openclaw/workspace/antfarm
./dist/cli/cli.js workflow install feature-dev
./dist/cli/cli.js workflow install bug-fix

# 2. Create XKG-specific agent cron scripts
echo ""
echo "2. Creating XKG agent scripts..."

# VPS Health Monitor - every 5 minutes
cat > "$PROJECT_DIR/agents/vps-health-monitor.sh" << 'SCRIPT'
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
SCRIPT
chmod +x "$PROJECT_DIR/agents/vps-health-monitor.sh"

# Version Check - every 30 minutes
cat > "$PROJECT_DIR/agents/vps-version-check.sh" << 'SCRIPT'
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
SCRIPT
chmod +x "$PROJECT_DIR/agents/vps-version-check.sh"

# Research Explorer - every 8 hours
cat > "$PROJECT_DIR/agents/research-neo4j.sh" << 'SCRIPT'
#!/bin/bash
# Neo4j Research - Explores integration possibilities
LOG_FILE="/home/molty/.openclaw/workspace/projects/x-knowledge-graph/logs/research-neo4j.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "Starting Neo4j research exploration..."

cd /home/molty/.openclaw/workspace/projects/x-knowledge-graph

# Read current schema
if [ -f schema_for_neo4j.json ]; then
    log "Found schema_for_neo4j.json - analyzing..."
    
    # Count nodes and edges
    NODE_COUNT=$(grep -o '"type":' schema_for_neo4j.json | wc -l)
    log "Schema has $NODE_COUNT node type entries"
    
    # Check if Neo4j integration already exists
    if [ -f neo4j_import.py ]; then
        log "neo4j_import.py already exists"
    else
        log "No neo4j_import.py - creating prototype..."
        cat > neo4j_import.py << 'PYTHON'
# Neo4j Import Prototype for X Knowledge Graph
# TODO: Implement based on schema_for_neo4j.json

def import_to_neo4j(graph_data: dict) -> bool:
    """
    Import XKG graph data to Neo4j.
    
    Steps:
    1. Connect to Neo4j (bolt://localhost:7687)
    2. Create constraints
    3. Import nodes (tweet, grok, action, topic)
    4. Import edges (extracts, belongs_to)
    5. Create indexes for queries
    """
    # Placeholder - implement based on schema_for_neo4j.json
    print("Neo4j import not yet implemented")
    return False

if __name__ == "__main__":
    import json
    with open("schema_for_neo4j.json") as f:
        data = json.load(f)
    import_to_neo4j(data)
PYTHON
        log "Created neo4j_import.py prototype"
    fi
else
    log "No schema_for_neo4j.json found"
fi

log "Research exploration complete"
SCRIPT
chmod +x "$PROJECT_DIR/agents/research-neo4j.sh"

# 3. Create cron entries
echo ""
echo "3. Creating cron entries..."

# Get current crontab
CRON=$(crontab -l 2>/dev/null || echo "")

# Add XKG agent crons
add_cron() {
    local schedule="$1"
    local command="$2"
    local comment="$3"
    
    if ! echo "$CRON" | grep -q "$comment"; then
        (echo "$CRON"; echo "$schedule $command  # $comment") | crontab -
        echo "✅ Added: $comment"
    else
        echo "✅ Already exists: $comment"
    fi
}

add_cron "*/5 * * * *" "$PROJECT_DIR/agents/vps-health-monitor.sh" "XKG VPS Health Monitor"
add_cron "*/30 * * * *" "$PROJECT_DIR/agents/vps-version-check.sh" "XKG Version Check"
add_cron "0 */8 * * *" "$PROJECT_DIR/agents/research-neo4j.sh" "XKG Neo4j Research"

# 4. Create agent workspace for feature development
echo ""
echo "4. Setting up XKG workspace..."
mkdir -p "$PROJECT_DIR/agents/workspace"

# Create a simple task launcher
cat > "$PROJECT_DIR/agents/task-launcher.sh" << 'SCRIPT'
#!/bin/bash
# Launch an antfarm workflow for XKG
# Usage: ./task-launcher.sh "Add Todoist export feature"

cd ~/.openclaw/workspace/antfarm
./dist/cli/cli.js workflow run feature-dev "$1"

echo ""
echo "Workflow started! Check status with:"
echo "  ./dist/cli/cli.js workflow status \"$1\""
SCRIPT
chmod +x "$PROJECT_DIR/agents/task-launcher.sh"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Crons created:"
crontab -l | grep XKG
echo ""
echo "Agent scripts:"
ls -la "$PROJECT_DIR/agents/"*.sh
echo ""
echo "Usage:"
echo "  Feature development: ./agents/task-launcher.sh \"Your feature\""
echo "  Manual health check: ./agents/vps-health-monitor.sh"
echo "  Manual version check: ./agents/vps-version-check.sh"
echo "  Run research: ./agents/research-neo4j.sh"
echo ""
echo "Antfarm workflows:"
./dist/cli/cli.js workflow list
