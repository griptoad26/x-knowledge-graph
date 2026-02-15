# X Knowledge Graph - Export Format Specification

## Overview
This document specifies the expected file formats for X (Twitter) and Grok exports that X Knowledge Graph can parse.

---

## X Export Format

### Expected Structure

```
x_export/
├── tweet.js      (required - main tweets)
├── like.js       (optional - likes)
└── reply.js      (optional - replies)
```

Or with a `data/` subfolder (Twitter's default export format):

```
x_export/
└── data/
    ├── tweet.js
    ├── like.js
    └── reply.js
```

### tweet.js Format

**JavaScript wrapper format (most common):**
```javascript
window.YTD.tweet.part0 = [
  {
    "tweet": {
      "id": "1234567890123456789",
      "text": "Your tweet text here",
      "created_at": "2024-01-15T10:30:00Z",
      "user": {
        "id": "9876543210",
        "screen_name": "username"
      },
      "in_reply_to_status_id": null,
      "conversation_id": "1234567890123456789",
      "entities": {
        "hashtags": [{"text": "coding"}],
        "urls": [],
        "mentions": []
      },
      "metrics": {
        "retweet_count": 0,
        "reply_count": 2,
        "like_count": 5,
        "quote_count": 0
      }
    }
  },
  // ... more tweets
]
```

**Or plain JSON array:**
```json
[
  {
    "id": "1234567890123456789",
    "text": "Your tweet text here",
    "created_at": "2024-01-15T10:30:00Z",
    "user": {"id": "9876543210"},
    "conversation_id": "1234567890123456789"
  }
]
```

### Fields Used by Parser

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Tweet ID |
| `text` | Yes | Tweet content |
| `created_at` | No | Timestamp |
| `user.id` | No | Author ID |
| `conversation_id` | No | Conversation thread ID |

---

## Grok Export Format

### Expected Structure

```
grok_export/
└── posts.json      (required)
```

### posts.json Format

```json
[
  {
    "id": "grok_001",
    "text": "Your message content here",
    "created_at": "2024-01-15T09:30:00Z",
    "author_id": "user_123",
    "conversation_id": "conv_001",
    "in_reply_to_id": null,
    "metrics": {
      "likes": 15,
      "shares": 3,
      "replies": 5
    },
    "entities": ["deployment", "monitoring"]
  },
  {
    "id": "grok_002",
    "text": "Another message",
    "created_at": "2024-01-15T14:22:00Z",
    "author_id": "user_123",
    "conversation_id": "conv_002",
    "in_reply_to_id": "grok_010",
    "metrics": {
      "likes": 8,
      "shares": 1,
      "replies": 2
    }
  }
  // ... more posts
]
```

### Fields Used by Parser

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Message ID |
| `text` | Yes | Message content |
| `created_at` | No | Timestamp |
| `author_id` | No | Author ID |
| `conversation_id` | No | Conversation thread ID |
| `in_reply_to_id` | No | Reply reference |

---

## Action Extraction

Both X and Grok exports support automatic action extraction:

### Patterns Detected

| Pattern | Example | Priority |
|---------|---------|----------|
| `TODO:` | "TODO: Review docs" | high |
| `need to` | "Need to finish by Friday" | medium |
| `remember to` | "Remember to backup" | medium |
| `going to` | "Going to refactor" | medium |
| `ASAP` / `urgent` | "This is urgent" | urgent |
| `don't forget` | "Don't forget to backup" | medium |

### Priority Mapping

| Detected | Mapped To |
|----------|-----------|
| urgent / ASAP / critical | urgent |
| TODO / need to / remember | high |
| going to / should / must | medium |
| general actions | low |

---

## Amazon Product Linking

Actions containing purchase keywords automatically get Amazon search links:

**Keywords detected:** buy, purchase, get, order, need

**Example:**
```
"buy a new wireless mouse"
→ Amazon link: https://www.amazon.com/s?k=wireless+mouse
```

---

## Testing

### Test Data Locations

| Export Type | Location |
|-------------|----------|
| X | `test_data/x_export/tweet.js` |
| Grok | `test_data/grok_export/posts.json` |

### Run Tests

```bash
# Test X export parsing
cd projects/x-knowledge-graph
python3 -c "
from core.xkg_core import KnowledgeGraph
kg = KnowledgeGraph()
result = kg.build_from_export('./test_data/x_export', 'x')
print(f'Tweets: {result[\"stats\"][\"total_tweets\"]}')
print(f'Actions: {result[\"stats\"][\"total_actions\"]}')
"

# Test Grok export parsing
python3 -c "
from core.xkg_core import KnowledgeGraph
kg = KnowledgeGraph()
result = kg.build_from_export('./test_data/grok_export', 'grok')
print(f'Messages: {result[\"stats\"][\"total_tweets\"]}')
print(f'Actions: {result[\"stats\"][\"total_actions\"]}')
"
```

---

## Troubleshooting

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "No data folder found" | Wrong path | Ensure path points to export folder, not individual files |
| "0 tweets parsed" | File not found or invalid JSON | Check tweet.js exists and is valid JSON |
| "JSONDecodeError" | JavaScript comments or invalid syntax | Remove `//` comments from file |
| Actions not extracted | Tweet text doesn't match patterns | Add action keywords (TODO, need to, etc.) |

### Validation Checklist

- [ ] Export folder exists at specified path
- [ ] tweet.js or posts.json exists
- [ ] File contains valid JSON (no comments)
- [ ] JSON has expected structure with `id` and `text` fields
- [ ] Tweet/content contains actionable language

---

## Version Compatibility

| XKG Version | X Format | Grok Format |
|-------------|----------|-------------|
| v0.4.32+ | tweet.js (YTD format) | posts.json |
| v0.4.0-31 | tweet.js (limited) | posts.json (limited) |

