#!/usr/bin/env python3
"""
Patch script to add proper timestamp parsing to xkg_core.py
Run: python3 patch_timestamps.py
"""

import re

# Read the original file
with open('core/xkg_core.py', 'r') as f:
    content = f.read()

# 1. Add timestamp parser function before KnowledgeGraph class
timestamp_parser = '''

def parse_timestamp(ts: str) -> str:
    """Parse various timestamp formats to ISO 8601"""
    if not ts:
        return ""
    
    # Already ISO format
    if re.match(r'^\\d{4}-\\d{2}-\\d{2}T', ts):
        return ts.split('.')[0] + 'Z' if 'Z' not in ts else ts.split('.')[0] + 'Z'
    
    formats = [
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%a %b %d %H:%M:%S %z %Y',
        '%Y-%m-%dT%H:%M:%S+0000',
    ]
    
    for fmt in formats:
        try:
            from datetime import datetime
            dt = datetime.strptime(ts.replace('+0000', '').replace('Z', ''), fmt)
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            continue
    
    return ts

'''

# Insert after the imports section
# Find the first class definition and insert before it
pattern = r'(class Tweet:)'
replacement = timestamp_parser + r'\\1'
content = re.sub(pattern, replacement, content, count=1)

# 2. Update export_for_d3 to use timestamp parser
old_export = '''    # Tweet nodes
    for tweet_id, tweet in self.tweets.items():
        nodes.append({
            'id': f'tweet_{tweet_id}',
            'type': 'tweet',
            'label': tweet.text[:50] + '...' if len(tweet.text) > 50 else tweet.text,
            'text': tweet.text,
            'topic': 'general',
            'source': 'x'
        })'''

new_export = '''    # Tweet nodes with parsed timestamps
    for tweet_id, tweet in self.tweets.items():
        nodes.append({
            'id': f'tweet_{tweet_id}',
            'type': 'tweet',
            'label': tweet.text[:50] + '...' if len(tweet.text) > 50 else tweet.text,
            'text': tweet.text,
            'topic': 'general',
            'source': 'x',
            'created_at': parse_timestamp(tweet.created_at),  # ← Parsed timestamp
            'author_id': tweet.author_id,
            'conversation_id': tweet.conversation_id or ''
        })'''

content = content.replace(old_export, new_export)

# 3. Update Grok post nodes
old_grok = '''        # Grok post nodes (separate from X tweets)
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

new_grok = '''        # Grok post nodes with parsed timestamps
        for post_id, post in self.posts.items():
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
                'created_at': parse_timestamp(post.created_at),  # ← Parsed timestamp
                'conversation_id': post.conversation_id or '',
                'conversation_title': conv_title,
                'author_id': post.author_id
            })'''

content = content.replace(old_grok, new_grok)

# Write the patched file
with open('core/xkg_core.py', 'w') as f:
    f.write(content)

print("✅ Patched core/xkg_core.py with:")
print("   • parse_timestamp() function")
print("   • Proper created_at parsing for tweets")
print("   • Proper created_at parsing for Grok posts")
print()
print("⚠️  Manual verification needed - check the file for correctness")

