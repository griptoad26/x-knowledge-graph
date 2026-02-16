# X Knowledge Graph - VPS Testing Standards

**Current Version:** v0.5.0  
**Testing Version:** v0.5.1  
**Last Updated:** 2026-02-16

---

## 1. Testing Environment

### VPS Access
```
IP: 66.179.191.93
User: Administrator
Path: /projects/x-knowledge-graph
Port: 51338
URL: http://66.179.191.93:51338
```

### Local Testing
```
URL: http://127.0.0.1:51338
Data Path: test_data/
```

---

## 2. Test Data Requirements

### Required Files
```
test_data/
├── x_export/
│   ├── tweet.js      (X posts export)
│   └── like.js       (X likes export)
└── grok_export/
    └── posts.json    (Grok conversations export)
```

### Test Data Specifications
| File | Min Items | Max Size |
|------|-----------|----------|
| tweet.js | 5 tweets | 50KB |
| like.js | 5 likes | 50KB |
| posts.json | 10 posts | 100KB |

---

## 3. Testing Checklist

### Phase 1: Application Launch
- [ ] Start app: `python main.py`
- [ ] Verify health endpoint: `curl http://localhost:51338/health`
- [ ] Check version in response
- [ ] Confirm no console errors

### Phase 2: Data Processing
- [ ] Upload tweet.js
- [ ] Upload like.js
- [ ] Upload posts.json
- [ ] Verify items extracted
- [ ] Verify actions detected
- [ ] Verify topics clustered

### Phase 3: Graph Visualization
- [ ] Nodes render correctly
- [ ] Edges display properly
- [ ] Zoom in/out works
- [ ] Pan/drag works
- [ ] Cluster expansion works

### Phase 4: Action Extraction
- [ ] TODO items detected
- [ ] Need to items detected
- [ ] ASAP items detected
- [ ] Follow up items detected
- [ ] Priority assigned correctly

### Phase 5: Export Features
- [ ] Todoist export works
- [ ] Amazon links generated
- [ ] JSON export works
- [ ] Markdown export works

---

## 4. Browser Testing

### Open Browser
```bash
# Windows
start http://localhost:51338

# macOS
open http://localhost:51338

# Linux
xdg-open http://localhost:51338
```

### Browser Console Checks
- [ ] No JavaScript errors
- [ ] Network requests successful
- [ ] WebSocket connected (if applicable)
- [ ] No CORS errors

### Responsive Testing
| Viewport | Width | Check |
|----------|-------|-------|
| Desktop | 1920px | Full UI |
| Laptop | 1440px | Full UI |
| Tablet | 768px | Responsive |
| Mobile | 375px | Mobile layout |

---

## 5. Automated Validation

### Run Validation Script
```bash
python validate.py
```

### Expected Results
```
Graph Population:     3/3 pass ✅
Action Extraction:    3/3 pass ✅
Topic Clustering:     3/3 pass ✅
Graph Structure:      4/4 pass ✅
Performance:          4/4 pass ✅
Sample Data:          2/2 pass ✅
TOTAL:               19/19 pass ✅
```

### Performance Targets
| Operation | Target | Max |
|-----------|--------|-----|
| Data load | < 2s | 3s |
| Graph render | < 3s | 5s |
| Action extract | < 2s | 3s |
| Topic cluster | < 2s | 3s |

---

## 6. VPS-Specific Tests

### Remote Health Check
```bash
curl http://66.179.191.93:51338/health
```

Expected response:
```json
{"status": "ok", "version": "v0.5.1"}
```

### Port Accessibility
```bash
# From local machine
telnet 66.179.191.93 51338

# Or
nc -zv 66.179.191.93 51338
```

### Process Check
```bash
# On VPS
ps aux | grep python
netstat -tlnp | grep 51338
```

---

## 7. Deployment Steps

### 1. Build Distribution
```bash
# On local machine
python build.py
# or
build.bat
```

### 2. Transfer to VPS
```bash
scp x-knowledge-graph-v0.5.1.tar administrator@66.179.191.93:/projects/
```

### 3. Deploy on VPS
```bash
ssh administrator@66.179.191.93
cd /projects/x-knowledge-graph
tar -xf x-knowledge-graph-v0.5.1.tar
python main.py &
```

### 4. Verify Deployment
```bash
curl http://localhost:51338/health
```

---

## 8. Test Data Examples

### Sample tweet.js
```javascript
window.YTD.tweet.part0 = [
  {
    "tweet": {
      "id": "123456789",
      "full_text": "TODO: Need to follow up on the project",
      "created_at": "2026-02-15",
      "in_reply_to_status_id": null
    }
  }
];
```

### Sample posts.json
```json
[
  {
    "id": "msg_123",
    "content": "ASAP: Complete the quarterly review",
    "timestamp": "2026-02-15T10:00:00Z"
  }
]
```

---

## 9. Issue Reporting

### Template
```markdown
## Issue: [Brief Description]

### Environment
- Version: v0.5.1
- OS: [Windows/Linux/macOS]
- Browser: [Chrome/Firefox/Safari]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Expected Result
[What should happen]

### Actual Result
[What actually happened]

### Screenshots
[Attach screenshots]

### Console Errors
[Copy any errors]
```

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| v0.5.0 | 2026-02-15 | Semantic search, bidirectional linking, analytics |
| v0.4.34 | 2026-02-15 | 434/434 tests pass, VPS validation |
| v0.4.33 | 2026-02-14 | Dynamic version reading |

---

## 11. Quick Test Commands

```bash
# 1. Start app
python main.py

# 2. Health check
curl http://localhost:51338/health

# 3. Run validation
python validate.py

# 4. Test with sample data
cp test_data/x_export/tweet.js ./x_export/
cp test_data/grok_export/posts.json ./

# 5. Stop app
pkill -f "python main.py"
```

---

*Test everything. Break nothing.*
