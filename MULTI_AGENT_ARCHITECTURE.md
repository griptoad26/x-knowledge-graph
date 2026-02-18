# X Knowledge Graph - Multi-Agent Architecture

## Problem Statement

Current: Single agent handles everything → downtime, slow iteration

Solution: 4 parallel agents covering different domains

---

## Agent Roles

| Agent | Responsibility | Work Pattern |
|-------|---------------|--------------|
| **Core Developer** | Features, bug fixes, code improvements | PR-based, needs review |
| **VPS/DevOps** | Deployment, monitoring, updates | Event-driven + cron |
| **Testing/QA** | Validation, benchmarks, regression tests | Continuous, automated |
| **Research/Explorer** | New integrations (Neo4j, embeddings, LLM) | Exploration-based |

---

## Proposed Agent Setup

### 1. Core Developer Agent
**Task:** Features and bug fixes
```
• Parse GitHub issues/tickets
• Implement features with tests
• Create PRs for review
• Update documentation
```

### 2. VPS/DevOps Agent  
**Task:** Deployment and infrastructure
```
• Monitor server health
• Deploy new versions
• Handle logs/errors
• Auto-restart on failure
```

### 3. Testing/QA Agent
**Task:** Quality assurance
```
• Run validation suite (434 tests)
• Performance benchmarks
• Browser testing
• Error regression detection
```

### 4. Research/Explorer Agent
**Task:** New capabilities
```
• Neo4j integration prototype
• LLM action extraction testing
• Embedding-based clustering
• New export format support

---

## Antfarm Workflow Definitions

Create in `/home/molty/.openclaw/workspace/antfarm/workflows/`:

```yaml
# xkg-core-dev.yaml
name: xkg-core-dev
description: XKG core development - features and fixes
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
  - id: pr-reviewer
    name: XKG Reviewer
    model: minimax/MiniMax-M2.5
    cron: "0 9 * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph

steps:
  - id: plan
    agent: planner
    output: plan.md
  - id: develop
    agent: developer
    depends: [plan]
    output: changes.patch
  - id: test
    agent: tester
    depends: [develop]
    output: test-results.json
  - id: review
    agent: pr-reviewer
    depends: [test]
    output: pr-draft.md

---

# xkg-vps-ops.yaml
name: xkg-vps-ops
description: XKG VPS operations - deployment and monitoring
agents:
  - id: deployer
    name: XKG Deployer
    model: minimax/MiniMax-M2.1
    cron: "*/30 * * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
  - id: monitor
    name: XKG Monitor
    model: minimax/MiniMax-M2.1
    cron: "*/5 * * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph

steps:
  - id: check-version
    agent: monitor
    output: version-check.json
  - id: check-health
    agent: monitor
    depends: [check-version]
    output: health-report.json
  - id: deploy
    agent: deployer
    depends: [check-health]
    output: deploy-result.json
  - id: notify
    agent: deployer
    depends: [deploy]
    output: notification-sent.json

---

# xkg-research.yaml
name: xkg-research
description: XKG research - new integrations and capabilities
agents:
  - id: neo4j-explorer
    name: Neo4j Explorer
    model: minimax/MiniMax-M2.5
    cron: "0 */8 * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph
  - id: llm-tester
    name: LLM Integration Tester
    model: minimax/MiniMax-M2.5
    cron: "0 */8 * * *"
    workspace: /home/molty/.openclaw/workspace/projects/x-knowledge-graph

steps:
  - id: research-neo4j
    agent: neo4j-explorer
    output: neo4j-prototype.md
  - id: research-llm-extraction
    agent: llm-tester
    output: llm-extraction-results.json
  - id: prototype
    agent: neo4j-explorer
    depends: [research-neo4j]
    output: neo4j-demo.py
  - id: evaluate
    agent: llm-tester
    depends: [research-llm-extraction, prototype]
    output: evaluation-report.md
```

---

## Immediate Actions

### 1. Install Antfarm Workflows
```bash
cd ~/.openclaw/workspace/antfarm
./dist/cli/cli.js install
```

### 2. Create XKG Workflows
```bash
cd ~/.openclaw/workspace/antfarm
mkdir -p workflows
# Create the YAML files above
```

### 3. Start Key Agents
```bash
# Core development
./dist/cli/cli.js workflow run xkg-core-dev "Implement Neo4j export feature"

# VPS monitoring  
./dist/cli/cli.js workflow run xkg-vps-ops "Monitor and deploy v0.5.1"

# Research
./dist/cli/cli.js workflow run xkg-research "Prototype Neo4j import"
```

---

## Parallel Workstreams

```
┌─────────────────────────────────────────────────────────────────┐
│                    X KNOWLEDGE GRAPH                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   CORE DEV   │  │   VPS OPS   │  │   TESTING   │         │
│  │              │  │              │  │              │         │
│  │ • Features  │  │ • Deploy    │  │ • 434 tests │         │
│  │ • Bug fixes  │  │ • Monitor   │  │ • Benchmarks│         │
│  │ • Refactor   │  │ • Restart   │  │ • Regression│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                 │                 │                       │
│         └────────────────┼─────────────────┘                       │
│                          │                                      │
│                    ┌─────▼─────┐                               │
│                    │  RESEARCH  │                               │
│                    │           │                               │
│                    │ • Neo4j    │                               │
│                    │ • LLM      │                               │
│                    │ • Embeddings│                               │
│                    └───────────┘                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Crons for Continuous Operation

```bash
# Core Developer - every 15 min
# Picks up issues, implements, creates PRs

# VPS Ops - every 5 min monitoring, 30 min deployment check
# Auto-deploys new versions

# Testing - every 15 min
# Runs validation suite, reports failures

# Research - every 8 hours
# Explores new capabilities, prototypes
```

---

## Shared Context

All agents share via:
- **Files:** `/home/molty/.openclaw/workspace/projects/x-knowledge-graph/`
- **Memory:** `memory/*.md`  
- **Database:** SQLite via antfarm

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Deployment time | < 5 min from PR merge |
| Test coverage | 100% of core functions |
| VPS uptime | 99.9% |
| Research iterations | 2-3 per week |
| Bug-to-fix time | < 24 hours |

---

## Next Steps

1. ✅ Design complete
2. ⏳ Install antfarm workflows
3. ⏳ Create XKG-specific workflow files
4. ⏳ Start core dev agent
5. ⏳ Start VPS monitoring agent
6. ⏳ Start research agent

Want me to create the workflow files and install them?
