#!/bin/bash
# Launch an antfarm workflow for XKG
# Usage: ./task-launcher.sh "Add Todoist export feature"

cd ~/.openclaw/workspace/antfarm
./dist/cli/cli.js workflow run feature-dev "$1"

echo ""
echo "Workflow started! Check status with:"
echo "  ./dist/cli/cli.js workflow status \"$1\""
