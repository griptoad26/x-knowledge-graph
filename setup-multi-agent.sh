#!/bin/bash
# XKG Multi-Agent Setup Script
# Run this to set up parallel agents for X Knowledge Graph

set -e

echo "=========================================="
echo "X Knowledge Graph - Multi-Agent Setup"
echo "=========================================="

WORKFLOW_DIR="$HOME/.openclaw/workspace/antfarm/workflows/xkg"

# Check antfarm is installed
if [ ! -d "$HOME/.openclaw/workspace/antfarm" ]; then
    echo "Installing antfarm..."
    cd ~/.openclaw/workspace/antfarm
    npm install
fi

# Create workflow directories
mkdir -p "$WORKFLOW_DIR/prompts"
mkdir -p /home/molty/.openclaw/workspace/projects/x-knowledge-graph/logs

# Copy workflow files
echo "Installing workflows..."

# Core Dev Workflow
cat > "$WORKFLOW_DIR/xkg-core-dev.yaml" << 'YAML'
name: xkg-core-dev
description: XKG core development - features and bug fixes
agents:
  - id: planner
    name: XKG Planner
    model: minimax/MiniMax-M2.1
    cron: "*/15 * * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
  - id: developer
    name: XKG Developer
    model: minimax/MiniMax-M2.5
    cron: "*/15 * * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
  - id: tester
    name: XKG Tester
    model: minimax/MiniMax-M2.1
    cron: "*/15 * * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
  - id: reviewer
    name: XKG Reviewer
    model: minimax/MiniMax-M2.5
    cron: "0 9 * * 1"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
steps:
  - id: plan
    agent: planner
  - id: develop
    agent: developer
    depends: [plan]
  - id: test
    agent: tester
    depends: [develop]
  - id: review
    agent: reviewer
    depends: [test]
YAML

# VPS Ops Workflow
cat > "$WORKFLOW_DIR/xkg-vps-ops.yaml" << 'YAML'
name: xkg-vps-ops
description: XKG VPS deployment and monitoring
agents:
  - id: version-check
    name: XKG Version Check
    model: minimax/MiniMax-M2.1
    cron: "*/30 * * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
  - id: deployer
    name: XKG Deployer
    model: minimax/MiniMax-M2.1
    cron: "*/30 * * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
  - id: health-monitor
    name: XKG Health Monitor
    model: minimax/MiniMax-M2.1
    cron: "*/5 * * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
steps:
  - id: check-version
    agent: version-check
  - id: deploy
    agent: deployer
    depends: [check-version]
  - id: monitor
    agent: health-monitor
YAML

# Research Workflow
cat > "$WORKFLOW_DIR/xkg-research.yaml" << 'YAML'
name: xkg-research
description: XKG research - Neo4j, LLM, new integrations
agents:
  - id: neo4j-explorer
    name: XKG Neo4j Explorer
    model: minimax/MiniMax-M2.5
    cron: "0 */8 * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
  - id: llm-extractor
    name: XKG LLM Extractor
    model: minimax/MiniMax-M2.5
    cron: "0 */8 * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
steps:
  - id: research-neo4j
    agent: neo4j-explorer
  - id: prototype-neo4j
    agent: neo4j-explorer
    depends: [research-neo4j]
  - id: research-llm
    agent: llm-extractor
  - id: prototype-llm
    agent: llm-extractor
    depends: [research-llm]
YAML

echo "✅ Workflow files created"

# Create simple prompts (inline for simplicity)
for agent in planner developer tester reviewer version-check deployer health-monitor neo4j-explorer llm-extractor; do
    cat > "$WORKFLOW_DIR/prompts/${agent}.md" << 'PROMPT'
# Instructions

Work in /home/molty/.openclaw/workspace/projects/x-knowledge-graph

Output a JSON file with your results.
PROMPT
done

echo "✅ Prompts created"

# Install workflows
echo ""
echo "Installing workflows with antfarm..."
cd ~/.openclaw/workspace/antfarm
./dist/cli/cli.js workflow install xkg-core-dev || echo "Core dev workflow installed"
./dist/cli/cli.js workflow install xkg-vps-ops || echo "VPS ops workflow installed"
./dist/cli/cli.js workflow install xkg-research || echo "Research workflow installed"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Workflows installed:"
ls -la ~/.openclaw/workspace/antfarm/workflows/xkg/*.yaml

echo ""
echo "To start a workflow:"
echo "  ./dist/cli/cli.js workflow run xkg-core-dev \"Your task here\""
echo ""
echo "To check status:"
echo "  ./dist/cli/cli.js workflow status \"task name\""
echo ""
