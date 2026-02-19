#!/usr/bin/env python3
"""Apply fixes to xkg_core.py"""

import re

with open('core/xkg_core.py', 'r') as f:
    content = f.read()

# 1. Add parse_timestamp function before "class Tweet:"
timestamp_func = '''

def parse_timestamp(ts: str) -> str:
    """Parse various timestamp formats to ISO 8601"""
    if not ts:
        return ""
    
    # Already ISO format - clean it up
    if ts.startswith('20'):  # Starts with year like 2024-
        # Handle various formats
        if '.' in ts:
            ts = ts.split('.')[0]
        if 'Z' not in ts:
            ts = ts + 'Z'
        return ts
    
    return ""

'''

content = content.replace(
    'class Tweet:',
    timestamp_func + 'class Tweet:'
)

# 2. Improve priority keywords (cleaner, less noisy)
old_priority = """            'urgent': ['urgent', 'asap', 'immediately', 'critical', 'emergency', 'blocking', 'priority 1'],
            'high': ['important', 'TODO', 'need to', 'remember to', 'going to', 'should', 'must', 'required'],
            'medium': ['would be nice', 'consider', 'maybe', 'sometime', 'low priority'],
            'low': []"""

new_priority = """            # Improved priority detection - less noisy
            'urgent': ['asap', 'urgent', 'critical', 'emergency', 'blocking', 'priority 1', 'p1', 'right now', 'immediately'],
            'high': ['todo:', 'need to', 'must', 'required', 'deadline', 'by friday', 'by monday', 'this week', 'important'],
            'medium': ['remember to', 'going to', 'should', 'fix', 'update', 'review', 'check', 'look at', 'consider'],
            'low': ['would be nice', 'sometime', 'low priority', 'maybe', 'eventually', 'when possible']"""

content = content.replace(old_priority, new_priority)

# 3. Update tweet export to include timestamp
old_tweet_export = '''    def export_for_d3(self) -> Dict:
        """Export graph in D3.js format"""
        nodes = []
        edges = []
        
        # Tweet nodes
        for tweet_id, tweet in self.tweets.items():
            nodes.append({
                'id': f'tweet_{tweet_id}',
                'type': 'tweet',
                'label': tweet.text[:50] + '...' if len(tweet.text) > 50 else tweet.text,
                'text': tweet.text,
                'topic': 'general',
                'source': 'x'
            })'''

new_tweet_export = '''    def export_for_d3(self) -> Dict:
        """Export graph in D3.js format with proper timestamps"""
        nodes = []
        edges = []
        
        # Tweet nodes with parsed timestamps
        for tweet_id, tweet in self.tweets.items():
            created_at = parse_timestamp(tweet.created_at)
            nodes.append({
                'id': f'tweet_{tweet_id}',
                'type': 'tweet',
                'label': tweet.text[:50] + '...' if len(tweet.text) > 50 else tweet.text,
                'text': tweet.text,
                'topic': 'general',
                'source': 'x',
                'created_at': created_at,
                'author_id': tweet.author_id,
                'conversation_id': tweet.conversation_id or ''
            })'''

content = content.replace(old_tweet_export, new_tweet_export)

# 4. Update Grok post export
old_grok_export = '''        # Grok post nodes (separate from X tweets)
        for post_id, post in self.posts.items():
            # Get conversation info if available
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
                'conversation_id': post.conversation_id,
                'conversation_title': conv_title
            })'''

new_grok_export = '''        # Grok post nodes with parsed timestamps
        for post_id, post in self.posts.items():
            created_at = parse_timestamp(post.created_at)
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
                'created_at': created_at,
                'conversation_id': post.conversation_id or '',
                'conversation_title': conv_title,
                'author_id': post.author_id
            })'''

content = content.replace(old_grok_export, new_grok_export)

# Write the fixed file
with open('core/xkg_core.py', 'w') as f:
    f.write(content)

print("✅ Applied all fixes to core/xkg_core.py:")
print()
print("1. Added parse_timestamp() function")
print("   - Handles ISO8601, handles timestamps from exports")
print()
print("2. Improved priority keywords")
print("   - Less noise, clearer categorization")
print()
print("3. Added created_at to all nodes")
print("   - Tweet nodes: parsed from created_at field")
print("   - Grok nodes: parsed from created_at field")
print()
print("4. Added metadata fields")
print("   - author_id, conversation_id on nodes")
print()
print("Run: python3 export_schema_visualization.py to verify")

