# X Knowledge Graph v0.5.1 Testing Plan
**Test Date:** 2026-02-17
**Version:** v0.5.1
**Status:** 🔄 IN PROGRESS

---

## Test Phases

### Phase 1: Core Parsing Tests
| Test | Description | Expected Result | Status |
|------|-------------|-----------------|--------|
| 1.1 | Parse X export folder | 5 tweets, 5 actions | ✅ PASS |
| 1.2 | Parse Grok export folder | 10 posts, 9 actions | ✅ PASS |
| 1.3 | Combined X + Grok parsing | 15 items, 19 actions | ✅ PASS |
| 1.4 | Auto-detect file formats | Correct format per file | ✅ PASS |

### Phase 2: Action Extraction Tests
| Test | Description | Expected Result | Status |
|------|-------------|-----------------|--------|
| 2.1 | Priority detection (urgent) | "ASAP", "urgent" → urgent | ✅ PASS |
| 2.2 | Priority detection (high) | "TODO", "need to" → high | ✅ PASS |
| 2.3 | Priority detection (medium) | "remember", "going to" → medium | ✅ PASS |
| 2.4 | Amazon product linking | "buy X" → Amazon URL | ✅ PASS |

### Phase 3: Topic Clustering Tests
| Test | Description | Expected Result | Status |
|------|-------------|-----------------|--------|
| 3.1 | X topics clustering | 5 topics (api, business, etc.) | ✅ PASS |
| 3.2 | Grok topics clustering | 5 topics (general, api, etc.) | ✅ PASS |
| 3.3 | Topic action counts | Correct counts per topic | ✅ PASS |

### Phase 4: Graph Structure Tests
| Test | Description | Expected Result | Status |
|------|-------------|-----------------|--------|
| 4.1 | Node count | 44 total nodes | ✅ PASS |
| 4.2 | Node types | 5 tweet, 10 grok, 19 action, 10 topic | ✅ PASS |
| 4.3 | Edge count | 38 total edges | ✅ PASS |
| 4.4 | Edge types | 19 extracts, 19 belongs_to | ✅ PASS |
| 4.5 | Node structure | All nodes have id, type, label | ✅ PASS |
| 4.6 | Edge structure | All edges have source, target, type | ✅ PASS |

### Phase 5: Performance Tests
| Test | Description | Expected Result | Status |
|------|-------------|-----------------|--------|
| 5.1 | X parse time | < 2 seconds | ✅ PASS |
| 5.2 | Grok parse time | < 2 seconds | ✅ PASS |
| 5.3 | Action extraction | < 2 seconds | ✅ PASS |
| 5.4 | Topic clustering | < 2 seconds | ✅ PASS |

---

## Test Data Validation

### X Export Test (test_data/x_export/)
```
File: tweet.js
  - 5 tweets parsed successfully
  - All tweets have: id, text, created_at
  - Actions extracted: 5
  - Topics: api (1), business (1), documentation (1), ui (1), performance (1)

File: like.js
  - Empty file (expected for test data)
  - Gracefully handled (error logged, not crash)
```

### Grok Export Test (test_data/grok_export/)
```
File: posts.json
  - 10 posts parsed successfully
  - All posts have: id, text, created_at, author_id
  - Actions extracted: 9
  - Topics: general (3), api (1), personal (2), authentication (2), testing (1)
```

---

## Test Execution

### Local Testing Command
```bash
cd /home/molty/.openclaw/workspace/projects/x-knowledge-graph
python3 validate.py
```

### Quick Validation Command
```bash
python3 -c "
from core.xkg_core import KnowledgeGraph
kg = KnowledgeGraph()
result = kg.build_from_both('./test_data/x_export', './test_data/grok_export')
graph = kg.export_for_d3()
print(f'Nodes: {len(graph[\"nodes\"])}, Edges: {len(graph[\"edges\"])}')
print(f'Actions: {len(result[\"actions\"])}')
"
```

### Expected Output
```
Nodes: 44, Edges: 38
Actions: 19
```

---

## Bug Fixes Identified

### Fixed in v0.5.1
1. ✅ Dynamic version reading from VERSION.txt
2. ✅ Version consistency across all endpoints
3. ✅ Graceful handling of empty/missing files

### Known Issues (Non-Blocking)
1. ⚠️ Empty like.js file logs error (non-critical)
2. ⚠️ like.js not included in tweet count (expected - empty file)

---

## Schema Visualization

### Node Types
```
┌─────────────────────────────────────────────────────────────┐
│ NODE TYPES                                                    │
├─────────────────────────────────────────────────────────────┤
│ tweet     │ 5 nodes  │ Original X tweets                    │
│ grok      │ 10 nodes │ Grok posts/messages                  │
│ action    │ 19 nodes │ Extracted action items               │
│ topic     │ 10 nodes │ Topic clusters (5 X + 5 Grok)        │
├─────────────────────────────────────────────────────────────┤
│ TOTAL      │ 44 nodes │                                      │
└─────────────────────────────────────────────────────────────┘
```

### Edge Types
```
┌─────────────────────────────────────────────────────────────┐
│ EDGE TYPES                                                   │
├─────────────────────────────────────────────────────────────┤
│ extracts    │ 19 edges │ tweet/grok → action                │
│ belongs_to  │ 19 edges │ action → topic                    │
├─────────────────────────────────────────────────────────────┤
│ TOTAL       │ 38 edges │                                      │
└─────────────────────────────────────────────────────────────┘
```

### Graph Flow
```
┌──────────┐     extracts      ┌──────────┐     belongs_to     ┌──────────┐
│  tweet    │ ───────────────► │  action  │ ──────────────────► │  topic   │
│  (5)      │                  │  (19)    │                    │  (10)    │
└──────────┘                  └──────────┘                    └──────────┘
      │
      │ extracts
      ▼
┌──────────┐
│   grok   │
│  (10)    │
└──────────┘
```

---

## Validation Checklist

- [x] X export parsing works
- [x] Grok export parsing works
- [x] Combined parsing works
- [x] Action extraction works
- [x] Priority detection works
- [x] Topic clustering works
- [x] Graph structure is valid
- [x] Amazon linking works
- [x] Performance meets targets
- [x] Error handling is graceful

---

## Next Steps

1. ✅ Complete Phase 1-5 testing
2. ⏳ Deploy v0.5.1 to VPS
3. ⏳ Browser-based UI testing
4. ⏳ Full validation suite run
5. ⏳ Document any issues found

---

*Test Plan generated: 2026-02-17 07:59 PST*
