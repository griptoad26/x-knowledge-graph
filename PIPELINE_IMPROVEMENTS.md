# X Knowledge Graph - Debug & Improvement Guide
**Date:** 2026-02-17
**Version:** v0.5.1+

---

## Quick Debug Helper

```python
# Add this to xkg_core.py or run standalone

import sys
sys.path.insert(0, 'core')
from xkg_core import find_all_export_files, detect_export_format
import os

def debug_format_detection(export_path):
    """Debug format detection for any export folder"""
    print(f'=== FORMAT DETECTION DEBUG: {export_path} ===')
    print()
    
    for f in find_all_export_files(export_path, ['*']):
        if os.path.isfile(f):
            fmt = detect_export_format(f)
            filename = os.path.basename(f)
            print(f'{filename:30} → {fmt}')
            
            if fmt == 'unknown':
                print(f'  ⚠️  UNKNOWN FORMAT - Peeking content:')
                with open(f) as fh:
                    content = fh.read(1000)
                    print(f'  {content[:300]}...')
            elif fmt == 'x':
                print(f'  ✅ X format detected')
            elif fmt == 'grok':
                print(f'  ✅ Grok format detected')
            print()

# Usage
debug_format_detection('./test_data/x_export')
debug_format_detection('./test_data/grok_export')
```

---

## Enhanced Priority Detection (Zero LLM Cost)

Replace the current priority keywords in `KnowledgeGraph.__init__()`:

```python
# Improved priority detection - less noisy
self.priority_keywords = {
    'urgent': [
        'asap', 'urgent', 'critical', 'emergency', 'blocking',
        'priority 1', 'p1', 'right now', 'immediately'
    ],
    'high': [
        'todo:', 'need to', 'must', 'required', 'deadline',
        'by friday', 'by monday', 'this week', 'important'
    ],
    'medium': [
        'remember to', 'going to', 'should', 'fix', 'update',
        'review', 'check', 'look at', 'consider'
    ],
    'low': [
        'would be nice', 'sometime', 'low priority', 'maybe',
        'eventually', 'when possible'
    ]
}
```

### Noise Reduction Rules

```python
def _find_actions_in_text(self, text: str, source_id: str, source_type: str) -> List[tuple]:
    """Find action items - reduced false positives"""
    actions = []
    text_lower = text.lower()
    
    # Only extract if action word is at sentence start or after punctuation
    sentences = re.split(r'[.!?\n]', text)
    
    for sentence in sentences:
        sentence = sentence.strip().lower()
        if len(sentence) < 15 or len(sentence) > 500:
            continue
            
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                # Only match at sentence boundaries to reduce noise
                pattern = rf'(?:^|\.\s+|\?\s+|!)\s*.{{0,20}}({re.escape(keyword)})'
                match = re.search(pattern, sentence)
                if match:
                    actions.append((sentence, priority))
                    break  # One priority per sentence
    
    return actions
```

---

## Conversation Extraction (New Node Type)

Add this to `FlexibleGrokParser._build_conversation()`:

```python
@dataclass
class ConversationNode:
    """Full conversation node for Neo4j import"""
    id: str
    title: str
    start_date: str
    end_date: str = ""
    message_count: int = 0
    participants: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': 'conversation',
            'label': self.title[:50] + '...' if len(self.title) > 50 else self.title,
            'title': self.title,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'message_count': self.message_count,
            'participants': self.participants
        }
```

### Enhanced Parser Logic

```python
def _build_conversation_with_links(self, conv_data: Dict):
    """Build conversation and link posts to it"""
    conv = conv_data.get('conversation', conv_data)
    conv_id = conv.get('id', '')
    
    # Collect all messages
    messages = []
    responses = conv_data.get('responses', conv_data.get('messages', []))
    
    participants = set()
    for resp in responses:
        resp_data = resp.get('response', resp)
        role = resp_data.get('sender', 'unknown')
        participants.add(role)
        
        timestamp = resp_data.get('create_time', '')
        messages.append({
            'role': role,
            'content': resp_data.get('message', ''),
            'timestamp': timestamp
        })
    
    # Create conversation node
    conversation = ConversationNode(
        id=f"conv_{conv_id}",
        title=conv.get('title', f"Conversation {conv_id[:8]}"),
        start_date=messages[0]['timestamp'] if messages else '',
        end_date=messages[-1]['timestamp'] if messages else '',
        message_count=len(messages),
        participants=list(participants)
    )
    
    self.conversations[conv_id] = conversation
    
    # Link each post to conversation
    for idx, msg in enumerate(messages):
        post_id = f"{conv_id}_{idx}"
        if post_id in self.posts:
            self.posts[post_id].conversation_id = f"conv_{conv_id}"
```

---

## Timestamp Addition (Future-Proof)

Update `export_for_d3()` to add ISO timestamps:

```python
def export_for_d3(self) -> Dict:
    """Export graph in D3.js format with timestamps"""
    nodes = []
    edges = []
    
    # Tweet nodes WITH timestamp
    for tweet_id, tweet in self.tweets.items():
        # Parse created_at to ISO format
        created_at_iso = self._parse_timestamp(tweet.created_at)
        
        nodes.append({
            'id': f'tweet_{tweet_id}',
            'type': 'tweet',
            'label': tweet.text[:50] + '...' if len(tweet.text) > 50 else tweet.text,
            'text': tweet.text,
            'topic': 'general',
            'source': 'x',
            'created_at': created_at_iso,  # ← NEW
            'author_id': tweet.author_id
        })
    
    # Grok post nodes WITH timestamp
    for post_id, post in self.posts.items():
        created_at_iso = self._parse_timestamp(post.created_at)
        
        conv_title = ''
        if post.conversation_id and post.conversation_id in self.grok_conversations:
            conv_title = self.grok_conversations[post.conversation_id].title
        
        nodes.append({
            'id': f'grok_{post_id}',
            'type': 'grok',
            'label': post.text[:50] + '...' if len(post.text) > 50 else post.text,
            'text': post.text,
            'topic': 'general',
            'source': 'grok',
            'created_at': created_at_iso,  # ← NEW
            'conversation_id': post.conversation_id,
            'conversation_title': conv_title
        })
    
    # Action nodes WITH timestamp
    for action in self.actions:
        nodes.append({
            'id': action.id,
            'type': 'action',
            'label': action.text[:40] + '...' if len(action.text) > 40 else action.text,
            'text': action.text,
            'priority': action.priority,
            'topic': action.topic,
            'source': action.source_type,
            'created_at': action.created_at,  # ← Already exists
            'amazon_link': action.amazon_link or ""
        })
    
    # ... rest unchanged
    
    return {'nodes': nodes, 'edges': edges}

def _parse_timestamp(self, ts: str) -> str:
    """Parse various timestamp formats to ISO"""
    if not ts:
        return datetime.now().isoformat()
    
    formats = [
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%a %b %d %H:%M:%S %z %Y'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(ts.replace('+0000', ''), fmt)
            return dt.isoformat()
        except ValueError:
            continue
    
    return ts  # Return original if parse fails
```

---

## Neo4j Import Script

Save as `neo4j_import.py`:

```python
#!/usr/bin/env python3
"""
Neo4j Import Script for X Knowledge Graph
Run after export_for_d3() to import into Neo4j

Prerequisites:
1. Neo4j Aura (free) or Desktop installed
2. APOC plugin enabled
3. Export saved: python3 -c "from core.xkg_core import KG; KG().export_for_d3()" > my_graph.json

Usage:
    python3 neo4j_import.py --uri bolt://localhost:7687 --user neo4j --password password
"""

import argparse
import json
from neo4j import GraphDatabase

def import_to_neo4j(uri, user, password, json_file='my_graph.json'):
    """Import D3 JSON into Neo4j"""
    
    with open(json_file) as f:
        data = json.load(f)
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Clear existing
        session.run("MATCH (n) DETACH DELETE n")
        
        # Create nodes
        for node in data['nodes']:
            props = {
                'id': node['id'],
                'label': node.get('label', ''),
                'text': node.get('text', ''),
                'type': node.get('type', ''),
                'source': node.get('source', ''),
                'created_at': node.get('created_at', ''),
                'priority': node.get('priority', ''),
                'topic': node.get('topic', ''),
                'conversation_id': node.get('conversation_id', ''),
                'message_count': node.get('message_count', 0)
            }
            # Remove None values
            props = {k: v for k, v in props.items() if v is not None}
            
            session.run(f"""
                CREATE (n:{node.get('type', 'node')} {{id: $id}})
                SET n += $props
            """, id=node['id'], props=props)
        
        # Create relationships
        for edge in data['edges']:
            session.run(f"""
                MATCH (a {{id: $source}})
                MATCH (b {{id: $target}})
                CREATE (a)-[r:{edge['type']}]->(b)
            """, source=edge['source'], target=edge['target'])
        
        # Create indexes
        session.run("CREATE INDEX FOR (n:action) ON (n.id)")
        session.run("CREATE INDEX FOR (n:action) ON (n.priority)")
        session.run("CREATE INDEX FOR (n:action) ON (n.topic)")
        session.run("CREATE INDEX FOR (n:action) ON (n.created_at)")
    
    driver.close()
    print(f"Imported {len(data['nodes'])} nodes and {len(data['edges'])} relationships")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--uri', default='bolt://localhost:7687')
    parser.add_argument('--user', default='neo4j')
    parser.add_argument('--password', required=True)
    args = parser.parse_args()
    
    import_to_neo4j(args.uri, args.user, args.password)
```

---

## LLM-Powered Action Extraction (Future)

```python
def extract_actions_with_llm(posts: List[Dict], api_key: str = None) -> List[Dict]:
    """
    Replace regex with LLM for much better action extraction.
    Even local Llama-3.2-1B works great for this.
    """
    import openai  # or use local model
    
    prompt = """Extract all action items from these posts. Return JSON array.
    
    For each action, return:
    - "text": The action text (clean, complete sentence)
    - "priority": URGENT, HIGH, MEDIUM, or LOW
    - "suggested_topic": One word topic (api, database, auth, etc.)
    - "entities": List of specific things mentioned
    
    Posts:
    {posts_json}
    
    Return ONLY valid JSON array, no markdown."""
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or local model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return json.loads(response.choices[0].message.content)
```

---

## Semantic Topic Clustering (Future)

```python
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN

def cluster_topics_semantic(actions: List[str], n_clusters=30):
    """
    Replace keyword buckets with embedding-based clustering.
    Gives 20-40 coherent topics instead of 10 overlapping ones.
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Get embeddings
    embeddings = model.encode(actions)
    
    # Cluster
    clusterer = HDBSCAN(min_cluster_size=3)
    labels = clusterer.fit_predict(embeddings)
    
    # Return topic assignments
    return {i: labels[i] for i in range(len(actions))}
```

---

## Monthly Trend Query (Plain JS)

```javascript
// In frontend/index.html - add to action list view
function showMonthlyTrends(actions) {
    const monthly = {};
    
    actions.forEach(action => {
        if (action.created_at) {
            const month = action.created_at.substring(0, 7); // YYYY-MM
            if (!monthly[month]) monthly[month] = { total: 0, urgent: 0, high: 0 };
            monthly[month].total++;
            if (action.priority === 'URGENT') monthly[month].urgent++;
            if (action.priority === 'HIGH') monthly[month].high++;
        }
    });
    
    // Render chart
    Object.entries(monthly).sort().forEach(([month, data]) => {
        console.log(`${month}: ${data.total} actions (${data.urgent} urgent, ${data.high} high)`);
    });
}
```

---

## Priority Fixes Summary

| Issue | Fix | Effort |
|-------|-----|--------|
| Format detection false unknowns | Add debug helper + more Grok checks | 5 min |
| Action extraction noise | Better regex boundaries + priority keywords | 10 min |
| Missing conversation links | Add conversation_id to all nodes | 15 min |
| No timestamps | Add ISO timestamps to all nodes | 10 min |
| Neo4j import | Create import script | 30 min |
| LLM action extraction | Replace regex with structured LLM call | 1 hour |
| Topic clustering | Embeddings + HDBSCAN | 2 hours |

---

## Next Steps

1. ✅ Add debug helper (run `python3 debug_format.py`)
2. ⏳ Update priority detection in `xkg_core.py`
3. ⏳ Add timestamps to all nodes
4. ⏳ Create Neo4j import script
5. ⏳ Test with real 1-month export
6. ⏳ Consider LLM action extraction for quality jump

---
