# XKG v0.5.4 Feature Specification Document

**Version:** v0.5.4  
**Date:** February 19, 2026  
**Status:** Draft

---

## 1. Executive Summary

This document defines the feature requirements for XKG v0.5.4, focusing on:
- Public API endpoints for external integrations
- Enhanced analytics dashboard capabilities
- Browser automation for web scraping and interaction
- Performance benchmarks and optimization targets

---

## 2. Public API Endpoints Design

### 2.1 Current API Assessment

**Existing Endpoints (v0.5.3):**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/select-folder` | POST | Select data folder |
| `/api/get-selected-folder` | GET | Get selected folder |
| `/api/parse-export` | POST | Parse export data |
| `/api/graph` | GET | Get graph data |
| `/api/actions` | GET | Get action items |
| `/api/topics` | GET | Get topics |
| `/api/grok-topics` | GET | Get Grok topics |
| `/api/grok-conversations` | GET | Get Grok conversations |
| `/api/flows` | GET | Get task flows |
| `/api/export-todoist` | POST | Export to Todoist |
| `/api/analytics/stats` | GET | Get analytics stats |
| `/api/analytics/chart/<type>` | GET | Generate chart |
| `/api/analytics/refresh` | POST | Refresh analytics |
| `/api/search` | POST | Semantic search |
| `/api/search/index` | POST | Create search index |
| `/api/search/stats` | GET | Get search stats |
| `/api/search/clear` | POST | Clear search index |
| `/api/export-pkm` | POST | Export to PKM systems |
| `/api/import-notion` | POST | Import from Notion |
| `/api/import-evernote` | POST | Import from Evernote |
| `/api/import-markdown` | POST | Import from Markdown |

### 2.2 Proposed New API Endpoints

#### 2.2.1 Graph Management API

```
GET    /api/v2/graph                    # Get full graph with pagination
GET    /api/v2/graph/<id>              # Get single node by ID
POST   /api/v2/graph/node              # Create new node
PUT    /api/v2/graph/node/<id>        # Update node
DELETE /api/v2/graph/node/<id>         # Delete node
POST   /api/v2/graph/edge              # Create relationship
DELETE /api/v2/graph/edge/<id>         # Delete relationship
GET    /api/v2/graph/traverse          # Traverse graph from node
GET    /api/v2/graph/path              # Find path between nodes
```

**Request/Response Examples:**

```json
// POST /api/v2/graph/node
{
  "type": "grok",
  "data": {
    "text": "Sample Grok post",
    "author_id": "user_123",
    "topic": "general"
  }
}

// Response
{
  "id": "grok_abc123",
  "type": "grok",
  "created_at": "2026-02-19T07:00:00Z"
}
```

#### 2.2.2 Neo4j Integration API

```
GET    /api/v2/neo4j/status            # Check Neo4j connection
POST   /api/v2/neo4j/connect           # Connect to Neo4j
POST   /api/v2/neo4j/sync              # Sync XKG to Neo4j
GET    /api/v2/neo4j/export            # Export graph to Neo4j format
POST   /api/v2/neo4j/query             # Execute Cypher query
GET    /api/v2/neo4j/schema            # Get Neo4j schema
```

#### 2.2.3 Actions API (Enhanced)

```
GET    /api/v2/actions                 # List actions with filters
POST   /api/v2/actions                 # Create action
GET    /api/v2/actions/<id>            # Get action details
PUT    /api/v2/actions/<id>            # Update action
DELETE /api/v2/actions/<id>            # Delete action
POST   /api/v2/actions/bulk            # Bulk operations
GET    /api/v2/actions/export/<format> # Export actions (json/csv)
```

**Filter Parameters:**
- `priority`: urgent, high, medium, low
- `status`: pending, in_progress, done
- `topic`: string
- `source`: grok, tweet, ai
- `date_from`: ISO date
- `date_to`: ISO date
- `page`: int (default: 1)
- `limit`: int (default: 50)

#### 2.2.4 Search API (Enhanced)

```
POST   /api/v2/search                  # Advanced search with filters
GET    /api/v2/search/suggest          # Get search suggestions
POST   /api/v2/search/history         # Get search history
DELETE /api/v2/search/history         # Clear search history
GET    /api/v2/search/related/<id>    # Find related content
```

#### 2.2.5 Webhooks API

```
POST   /api/v2/webhooks                # Register webhook
GET    /api/v2/webhooks                # List webhooks
DELETE /api/v2/webhooks/<id>           # Delete webhook
GET    /api/v2/webhooks/<id>/logs      # Get webhook execution logs
```

**Webhook Events:**
- `action.created`
- `action.updated`
- `action.completed`
- `graph.node_created`
- `graph.node_updated`
- `import.complete`
- `export.complete`

### 2.3 API Versioning Strategy

| Version | Status | Description |
|---------|--------|-------------|
| v1 | Deprecated | Original endpoints |
| v2 | Current | New structured endpoints |
| v2 (with suffix) | Experimental | Feature-specific endpoints |

**Backward Compatibility:**
- v1 endpoints maintained for 6 months
- Deprecation warnings in response headers
- Migration guide provided

### 2.4 Authentication & Rate Limiting

```python
# Rate limits (per API key)
RATE_LIMITS = {
    'free': {'requests': 100, 'window': 'minute'},
    'pro': {'requests': 1000, 'window': 'minute'},
    'enterprise': {'unlimited', 'window': 'minute'}
}

# Auth headers
HEADERS = {
    'X-API-Key': '<your-api-key>',
    'Authorization': 'Bearer <your-token>'
}
```

---

## 3. Analytics Dashboard Requirements

### 3.1 Dashboard Components

#### 3.1.1 Overview Widget

```
┌─────────────────────────────────────────────────────┐
│  📊 Knowledge Graph Overview                         │
├─────────────────────────────────────────────────────┤
│  Nodes: 1,234  │  Edges: 5,678  │  Actions: 89      │
│  Topics: 45    │  Conversations: 12               │
└─────────────────────────────────────────────────────┘
```

**Metrics:**
- Total node count with trend
- Total edge count with trend
- Action completion rate
- Content growth rate (nodes/week)

#### 3.1.2 Activity Timeline

```
📈 Activity Over Time
   |
   |         ██
   |       █████
   |     █████████
   |   ████████████
   +───────────────────────
    Jan  Feb  Mar  Apr
```

**Features:**
- Time range selector (7d, 30d, 90d, 1y, all)
- Granularity: hour, day, week, month
- Node type breakdown (tweets, actions, topics)
- Export as PNG/SVG

#### 3.1.3 Topic Distribution

```
🍕 Topic Distribution (Top 10)
  general:     ████████████░░░░ 45%
  tech:        ████████░░░░░░░░ 30%
  personal:    ████░░░░░░░░░░░░ 15%
  finance:     ██░░░░░░░░░░░░░░  8%
  other:       █░░░░░░░░░░░░░░░  2%
```

**Features:**
- Pie chart with interactive legend
- Drill-down by topic
- Filter by date range
- Topic trend comparison

#### 3.1.4 Action Dashboard

```
✅ Action Items
┌─────────────────────────────────────┐
│ Priority    │ Total │ Done │ Rate   │
├─────────────────────────────────────┤
│ 🔴 Urgent   │    12 │   8  │ 67%    │
│ 🟠 High     │    34 │  21  │ 62%    │
│ 🟡 Medium   │    78 │  45  │ 58%    │
│ 🟢 Low      │    56 │  42  │ 75%    │
└─────────────────────────────────────┘
```

**Features:**
- Priority breakdown
- Status distribution
- Overdue actions highlight
- Export to Todoist/CSV

#### 3.1.5 Source Breakdown

```
📱 Content Sources
  Twitter/X:    ████████████████  52%
  Grok:         ████████████░░░░  35%
  AI Exports:   ████░░░░░░░░░░░░  10%
  Other:        ██░░░░░░░░░░░░░░   3%
```

#### 3.1.6 LLM Extraction Stats

```
🤖 LLM Action Extraction
  Total Extractions:    1,234
  Accuracy (est):       84.6%
  Confidence Avg:      0.87
  Manual Reviews:       45
```

**Features:**
- Extraction volume over time
- Confidence score distribution
- Manual review queue

#### 3.1.7 Search Analytics

```
🔍 Search Statistics
  Total Searches:       5,678
  Avg Results:          12.3
  No Results:           234
  Top Queries:
    1. "project planning" (234)
    2. "action items" (198)
    3. "meeting notes" (156)
```

### 3.2 Dashboard Configuration

```python
# Dashboard Config Schema
{
  "widgets": [
    {"id": "overview", "enabled": True, "position": {"x": 0, "y": 0}},
    {"id": "activity_timeline", "enabled": True, "position": {"x": 0, "y": 1}},
    {"id": "topic_distribution", "enabled": True, "position": {"x": 1, "y": 0}},
    {"id": "action_dashboard", "enabled": True, "position": {"x": 1, "y": 1}},
    {"id": "source_breakdown", "enabled": True, "position": {"x": 2, "y": 0}},
    {"id": "llm_stats", "enabled": True, "position": {"x": 2, "y": 1}},
    {"id": "search_analytics", "enabled": False, "position": {"x": 3, "y": 0}}
  ],
  "refresh_interval": 300,  # seconds
  "theme": "dark|light",
  "date_range": "30d"
}
```

### 3.3 Export Options

| Format | Description | Use Case |
|--------|-------------|----------|
| PNG | High-res chart image | Reports, presentations |
| SVG | Vector format | Print, editing |
| JSON | Raw data | Further analysis |
| CSV | Tabular data | Spreadsheets |
| PDF | Full dashboard | Documentation |

---

## 4. Browser Automation Capabilities

### 4.1 Use Cases

1. **Web Scraping for Knowledge Import**
   - Extract content from web pages
   - Follow pagination and links
   - Handle JavaScript-rendered content

2. **Automated Interaction**
   - Form filling for logins
   - Button clicks and navigation
   - Authentication flows

3. **Screenshot Generation**
   - Visual documentation
   - Error reporting
   - Dashboard snapshots

4. **Headless Browser Testing**
   - Verify web UI functionality
   - Performance monitoring
   - Accessibility checks

### 4.2 Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser Automation Layer                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Playwright  │  │  Selenium    │  │   Puppeteer         │ │
│  │ (Primary)   │  │  (Backup)    │  │   (Node.js only)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  XKG Browser Controller                             │   │
│  │  - Navigation control                                │   │
│  │  - Content extraction                               │   │
│  │  - Form handling                                    │   │
│  │  - Screenshot capture                               │   │
│  │  - Error handling & retries                        │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Task Queue & Scheduler                             │   │
│  │  - Rate limiting                                    │   │
│  │  - Retry logic                                      │   │
│  │  - Progress tracking                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Implementation Plan

#### 4.3.1 Core Browser Module

```python
# browser_controller.py

class BrowserController:
    """Main browser automation controller"""
    
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.browser = None
        self.context = None
        self.page = None
    
    async def launch(self):
        """Launch browser with specified options"""
        self.browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport=self.config.viewport,
            user_agent=self.config.user_agent
        )
        self.page = await self.context.new_page()
    
    async def navigate(self, url: str, wait_until='domcontentloaded'):
        """Navigate to URL with optional waiting"""
        await self.page.goto(url, wait_until=wait_until)
    
    async def extract_content(self, selectors: List[Selector]) -> Dict:
        """Extract content using CSS/XPath selectors"""
        content = {}
        for selector in selectors:
            elements = await self.page.query_selector_all(selector.css)
            content[selector.name] = [self._parse_element(el) for el in elements]
        return content
    
    async def take_screenshot(self, path: str, full_page=False):
        """Capture screenshot"""
        await self.page.screenshot(
            path=path,
            full_page=full_page
        )
    
    async def fill_form(self, form_data: Dict):
        """Fill and submit form"""
        for field, value in form_data.items():
            await self.page.fill(f'[name="{field}"]', value)
        await self.page.click('button[type="submit"]')
```

#### 4.3.2 Web Scraper Module

```python
# web_scraper.py

class WebScraper:
    """Web scraping with rate limiting and error handling"""
    
    def __init__(self, controller: BrowserController):
        self.controller = controller
        self.rate_limiter = RateLimiter(max_requests=10, per_second=1)
        self.retry_handler = RetryHandler(max_retries=3, backoff=2)
    
    async def scrape_url(
        self,
        url: str,
        selectors: List[Selector],
        options: ScrapeOptions
    ) -> ScrapeResult:
        """Scrape a single URL"""
        async with self.rate_limiter:
            return await self.retry_handler.execute(
                self._do_scrape, url, selectors, options
            )
    
    async def scrape_sitemap(
        self,
        sitemap_url: str,
        selectors: List[Selector],
        max_pages: int = 100
    ) -> List[ScrapeResult]:
        """Scrape all URLs from sitemap"""
        urls = await self._get_sitemap_urls(sitemap_url)
        results = []
        for url in urls[:max_pages]:
            result = await self.scrape_url(url, selectors, ScrapeOptions())
            results.append(result)
        return results
```

#### 4.3.3 Authentication Module

```python
# auth_handler.py

class AuthHandler:
    """Handle authentication flows"""
    
    SUPPORTED_PROVIDERS = ['oauth2', 'basic', 'cookie', 'token']
    
    async def login(
        self,
        page: Page,
        provider: str,
        credentials: Dict
    ) -> bool:
        """Perform login with specified provider"""
        if provider == 'oauth2':
            return await self._oauth2_login(page, credentials)
        elif provider == 'basic':
            return await self._basic_login(page, credentials)
        elif provider == 'cookie':
            return await self._cookie_login(page, credentials)
        return False
    
    async def _oauth2_login(self, page, credentials):
        """OAuth2 login flow"""
        await page.goto(credentials['auth_url'])
        await page.fill('input[name="email"]', credentials['email'])
        await page.click('button[type="submit"]')
        # Handle OAuth redirect...
```

### 4.4 API Endpoints for Browser Automation

```
POST   /api/v2/browser/launch           # Launch browser instance
POST   /api/v2/browser/navigate         # Navigate to URL
POST   /api/v2/browser/scrape           # Scrape content
POST   /api/v2/browser/screenshot       # Take screenshot
POST   /api/v2/browser/fill-form        # Fill form
GET    /api/v2/browser/status           # Get browser status
POST   /api/v2/browser/close            # Close browser
POST   /api/v2/browser/screenshot/dashboard  # Dashboard screenshot
```

### 4.5 Use Case Examples

#### 4.5.1 Import Blog Content

```python
# Extract articles from a blog
selectors = [
    Selector(name='title', css='h1.post-title'),
    Selector(name='content', css='div.post-content'),
    Selector(name='date', css='time.post-date'),
    Selector(name='author', css='span.author-name')
]

results = await scraper.scrape_url(
    url='https://example-blog.com/articles',
    selectors=selectors,
    options=ScrapeOptions(wait_for_selector='div.post-content')
)
```

#### 4.5.2 Monitor Competitor Pricing

```python
# Scrape pricing pages and track changes
pricing_selectors = [
    Selector(name='product', css='div.product-name'),
    Selector(name='price', css='span.price-current'),
    Selector(name='availability', css='span.in-stock')
]

async def monitor_pricing(product_urls):
    for url in product_urls:
        current = await scraper.scrape_url(url, pricing_selectors)
        previous = await db.get_last_price(url)
        if current != previous:
            await alert_handler.send_price_alert(current, previous)
```

---

## 5. Performance Benchmarks

### 5.1 Benchmark Categories

#### 5.1.1 Import Performance

| Operation | Current (v0.5.3) | Target (v0.5.4) | Unit |
|-----------|-------------------|-----------------|------|
| Parse 1000 tweets | ~5s | ~3s | seconds |
| Parse Grok export (100 posts) | ~2s | ~1s | seconds |
| Import AI conversation | ~500ms | ~200ms | milliseconds |
| Process markdown folder (100 files) | ~10s | ~5s | seconds |
| Full import (mixed sources) | ~30s | ~15s | seconds |

#### 5.1.2 Graph Operations

| Operation | Current | Target | Unit |
|-----------|---------|--------|------|
| Node creation (single) | ~10ms | ~5ms | milliseconds |
| Edge creation (single) | ~10ms | ~5ms | milliseconds |
| Full graph load | ~2s | ~1s | seconds |
| Path finding (100 nodes) | ~100ms | ~50ms | milliseconds |
| Graph traversal (BFS) | ~50ms | ~25ms | milliseconds |

#### 5.1.3 Search Performance

| Operation | Current | Target | Unit |
|-----------|---------|--------|------|
| Semantic search (1000 items) | ~200ms | ~100ms | milliseconds |
| Keyword search | ~10ms | ~5ms | milliseconds |
| Full-text search | ~50ms | ~25ms | milliseconds |
| Index creation (1000 items) | ~2s | ~1s | seconds |

#### 5.1.4 Analytics Performance

| Operation | Current | Target | Unit |
|-----------|---------|--------|------|
| Stats generation | ~100ms | ~50ms | milliseconds |
| Chart rendering | ~500ms | ~200ms | milliseconds |
| Dashboard load | ~1s | ~500ms | milliseconds |
| Export to PNG | ~2s | ~1s | seconds |

#### 5.1.5 Memory Usage

| Scenario | Current | Target | Unit |
|----------|---------|--------|------|
| Idle (no data) | ~50MB | ~40MB | megabytes |
| 10k nodes loaded | ~200MB | ~150MB | megabytes |
| 100k nodes loaded | ~800MB | ~600MB | megabytes |
| Peak during import | ~500MB | ~350MB | megabytes |

#### 5.1.6 API Response Times

| Endpoint | Current P95 | Target P95 | Unit |
|----------|-------------|------------|------|
| /api/health | ~5ms | ~2ms | milliseconds |
| /api/graph | ~100ms | ~50ms | milliseconds |
| /api/actions | ~50ms | ~25ms | milliseconds |
| /api/analytics/stats | ~100ms | ~50ms | milliseconds |
| /api/search | ~200ms | ~100ms | milliseconds |

### 5.2 Benchmarking Tools

```python
# benchmark_runner.py

import time
import statistics
from typing import Callable, Any

class BenchmarkRunner:
    """Run and report benchmarks"""
    
    def __init__(self, iterations=100, warmup=10):
        self.iterations = iterations
        self.warmup = warmup
    
    def benchmark(self, func: Callable, *args, **kwargs) -> Dict:
        """Run benchmark and return statistics"""
        results = []
        
        # Warmup
        for _ in range(self.warmup):
            func(*args, **kwargs)
        
        # Actual benchmark
        for _ in range(self.iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            results.append(elapsed)
        
        return {
            'mean': statistics.mean(results),
            'median': statistics.median(results),
            'p95': sorted(results)[int(len(results) * 0.95)],
            'p99': sorted(results)[int(len(results) * 0.99)],
            'min': min(results),
            'max': max(results),
            'std': statistics.stdev(results)
        }
```

### 5.3 Performance Monitoring

```python
# performance_monitor.py

class PerformanceMonitor:
    """Continuous performance monitoring"""
    
    METRICS = [
        'cpu_percent',
        'memory_percent',
        'response_time',
        'import_duration',
        'search_duration'
    ]
    
    def __init__(self, sample_interval=60):
        self.interval = sample_interval
        self.metrics_buffer = defaultdict(list)
    
    def record_response_time(self, endpoint: str, duration: float):
        self.metrics_buffer[f'response_time.{endpoint}'].append(duration)
    
    def get_report(self) -> Dict:
        """Generate performance report"""
        report = {}
        for metric, values in self.metrics_buffer.items():
            if values:
                report[metric] = {
                    'mean': statistics.mean(values),
                    'p95': sorted(values)[int(len(values) * 0.95)],
                    'samples': len(values)
                }
        return report
```

### 5.4 Optimization Strategies

#### 5.4.1 Caching Layer

```python
# Implement LRU cache for frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_graph_stats_cached(graph_id: str) -> Dict:
    """Cached graph stats"""
    return calculate_graph_stats(graph_id)
```

#### 5.4.2 Async Processing

```python
# Use async/await for I/O operations
import asyncio

async def import_multiple_sources(sources: List[Source]):
    """Import multiple sources concurrently"""
    tasks = [import_source(source) for source in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

#### 5.4.3 Database Optimization

```python
# Add indexes for common queries
CREATE INDEX idx_actions_priority ON :Action(priority);
CREATE INDEX idx_actions_status ON :Action(status);
CREATE INDEX idx_actions_topic ON :Action(topic);
CREATE INDEX idx_grok_created ON :Grok(created_at);
```

---

## 6. Implementation Roadmap

### Phase 1: API Foundation (Week 1)
- [ ] Design API schema (OpenAPI 3.0)
- [ ] Implement v2 endpoints for graph operations
- [ ] Add authentication middleware
- [ ] Implement rate limiting
- [ ] Create API documentation

### Phase 2: Analytics Dashboard (Week 2)
- [ ] Enhance analytics engine
- [ ] Add new dashboard widgets
- [ ] Implement dashboard configuration UI
- [ ] Add export functionality
- [ ] Performance optimization

### Phase 3: Browser Automation (Week 3)
- [ ] Implement browser controller
- [ ] Add web scraping module
- [ ] Implement authentication handling
- [ ] Create browser API endpoints
- [ ] Add rate limiting for scraping

### Phase 4: Performance (Week 4)
- [ ] Implement benchmarking suite
- [ ] Optimize critical paths
- [ ] Add caching layer
- [ ] Performance testing
- [ ] Documentation updates

---

## 7. Testing Requirements

### 7.1 Unit Tests
- API endpoint tests (90% coverage)
- Analytics calculation tests
- Browser controller tests
- Performance benchmark tests

### 7.2 Integration Tests
- Full import workflow tests
- API authentication tests
- Browser automation E2E tests
- Dashboard rendering tests

### 7.3 Performance Tests
- Load testing (100 concurrent users)
- Stress testing (10x normal load)
- Endurance testing (24-hour run)

---

## 8. Dependencies

```txt
# New dependencies for v0.5.4
playwright>=1.40.0          # Browser automation
selenium>=4.15.0           # Browser automation (backup)
openapi-spec-validator>=0.6.0  # API validation
pytest-asyncio>=0.21.0     # Async testing
locust>=2.17.0             # Load testing
redis>=5.0.0               # Caching layer (optional)
```

---

## 9. Security Considerations

1. **API Security**
   - API key rotation
   - Request validation
   - Output sanitization
   - CORS configuration

2. **Browser Security**
   - Sandboxed browser execution
   - Resource limits
   - No sensitive data logging
   - Proxy support

3. **Data Security**
   - Encrypted storage
   - Secure credential handling
   - Audit logging

---

## 10. Success Criteria

- [ ] All v2 API endpoints functional and documented
- [ ] Dashboard loads in <500ms
- [ ] Browser automation handles 5+ concurrent scrapes
- [ ] Performance targets met (see Section 5)
- [ ] 90% test coverage
- [ ] API documentation complete

---

**Document Version:** 0.1  
**Last Updated:** 2026-02-19  
**Next Review:** 2026-02-26
