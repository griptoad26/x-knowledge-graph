# X Knowledge Graph - Export Format Specification

## Overview
This document specifies the expected file formats for X (Twitter), Grok, and AI (ChatGPT, Claude, Gemini) exports that X Knowledge Graph can parse.

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

## AI Export Formats

### OpenAI ChatGPT Export

#### HTML Export Format (from ChatGPT website)
```
chatgpt_export/
└── conversations.html    (or index.html)
```

**Detected by:** HTML structure with conversation items, `data-role` attributes

#### JSON Export Format (from API or data export)
```
chatgpt_export/
└── conversations.json
```

**JSON Structure:**
```json
{
  "mapping": {
    "msg_1": {
      "message": {
        "id": "msg_1",
        "author": {"role": "user"},
        "create_time": 1705312800,
        "content": {"parts": ["Hello, help me with..."]}
      }
    },
    "msg_2": {
      "message": {
        "id": "msg_2",
        "author": {"role": "assistant"},
        "create_time": 1705312850,
        "content": {"parts": ["Sure! Here's what you need..."]}
      }
    }
  },
  "conversation_id": "conv_abc123",
  "title": "My ChatGPT Conversation",
  "create_time": 1705312800,
  "update_time": 1705312900,
  "model_slug": "gpt-4"
}
```

**Detection Keywords:**
- `"mapping"` - Main mapping object
- `"conversation_id"` - Conversation identifier
- `"create_time"` / `"update_time"` - Unix timestamps
- `"content": {"parts": [...]}` - Message structure

---

### Anthropic Claude Export

```
claude_export/
└── conversations.json    (or export.json)
```

**JSON Structure:**
```json
[
  {
    "uuid": "chat-001",
    "title": "Code Review Session",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T11:30:00Z",
    "messages": [
      {
        "uuid": "msg_001",
        "role": "human",
        "content": "Can you review my Python code?",
        "created_at": "2024-01-15T10:00:00Z"
      },
      {
        "uuid": "msg_002",
        "role": "assistant",
        "content": "Sure! I can see a few issues to fix...",
        "created_at": "2024-01-15T10:05:00Z"
      }
    ],
    "metadata": {
      "model": "claude-2"
    }
  }
  // ... more conversations
]
```

**Detection Keywords:**
- `"uuid"` - Unique identifier
- `"human"` / `"assistant"` roles
- `"messages"` array with conversation
- `"chat_messages"` alternative format

---

### Google Gemini Export

```
gemini_export/
└── conversations.json    (or gemini_export.json)
```

**JSON Structure:**
```json
{
  "id": "gemini_001",
  "title": "Research Discussion",
  "createTime": "2024-01-15T09:00:00Z",
  "updateTime": "2024-01-15T10:30:00Z",
  "contents": [
    {
      "role": "user",
      "parts": [
        {"text": "Help me research quantum computing"}
      ],
      "createTime": "2024-01-15T09:00:00Z"
    },
    {
      "role": "model",
      "parts": [
        {"text": "Quantum computing uses qubits instead of..."}
      ],
      "createTime": "2024-01-15T09:05:00Z"
    }
  ],
  "metadata": {
    "model": "gemini-pro"
  }
}
```

**Detection Keywords:**
- `"contents"` array with conversation
- `"role": "user"` / `"role": "model"`
- `"parts": [{"text": "..."}]` - Message structure
- `"createTime"` / `"updateTime"` - ISO timestamps

---

## Action Extraction

All export formats support automatic action extraction:

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
| AI (ChatGPT) | `test_data/ai_export/chatgpt/conversations.json` |
| AI (Claude) | `test_data/ai_export/claude/conversations.json` |
| AI (Gemini) | `test_data/ai_export/gemini/conversations.json` |

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
print(f'Messages: {result[\"stats\"][\"total_posts\"]}')
print(f'Actions: {result[\"stats\"][\"total_actions\"]}')
"

# Test AI export parsing
python3 -c "
from core.xkg_core import KnowledgeGraph
kg = KnowledgeGraph()
result = kg.build_from_export('./test_data/ai_export', 'ai')
print(f'AI Conversations: {result[\"stats\"][\"total_ai_conversations\"]}')
print(f'Messages: {result[\"stats\"][\"total_messages\"]}')
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
| Actions not extracted | Tweet/text doesn't match patterns | Add action keywords (TODO, need to, etc.) |
| AI exports not detected | Wrong format or missing keywords | Check file has expected structure |

### AI Export Detection Tips

**ChatGPT:** Look for `mapping` field or `conversation_id` in JSON files

**Claude:** Look for `uuid` field and `human`/`assistant` roles

**Gemini:** Look for `contents` array with `role` and `parts` fields

### Validation Checklist

- [ ] Export folder exists at specified path
- [ ] Required file(s) exist
- [ ] File contains valid JSON/HTML
- [ ] JSON has expected structure with key fields
- [ ] Content contains actionable language (for action extraction)

---

## Version Compatibility

| XKG Version | X Format | Grok Format | AI Formats |
|-------------|----------|-------------|------------|
| v0.4.35+ | tweet.js (YTD format) | posts.json | ChatGPT, Claude, Gemini |
| v0.4.32-34 | tweet.js (YTD format) | posts.json | - |

