#!/usr/bin/env python3
"""
Grok Parser - Extract conversations from Grok JSON exports
"""

import json
import os
import hashlib
from collections import defaultdict


class GrokParser:
    """Parse Grok conversation JSON files"""
    
    def __init__(self):
        self.conversations = {}
        self.conversation_map = defaultdict(list)
    
    def parse(self, data):
        """
        Main entry point for parsing Grok data
        Handles various Grok export formats
        """
        # Auto-detect format
        if isinstance(data, list):
            return self._parse_list(data)
        elif isinstance(data, dict):
            if 'conversations' in data:
                return self._parse_conversations_array(data['conversations'])
            elif 'results' in data:
                return self._parse_results(data['results'])
            elif 'messages' in data:
                return self._parse_messages(data['messages'])
            else:
                return self._parse_dict(data)
        return []
    
    def _parse_list(self, items):
        """Parse a list of items"""
        conversations = []
        for item in items:
            conv = self._parse_single(item)
            if conv:
                conversations.append(conv)
        return conversations
    
    def _parse_conversations_array(self, conversations_data):
        """Parse conversations array"""
        # Check for new Grok format: {'conversation': {...}, 'responses': [...]}
        if conversations_data and isinstance(conversations_data[0], dict):
            if 'conversation' in conversations_data[0] and 'responses' in conversations_data[0]:
                return self._parse_new_grok_format(conversations_data)
        
        return [self._parse_single(c) for c in conversations_data if c]
    
    def _parse_new_grok_format(self, conversations_data):
        """Parse new Grok format with conversation/responses structure"""
        conversations = []
        
        for item in conversations_data:
            if not item or 'conversation' not in item:
                continue
            
            conv_meta = item['conversation']
            responses = item.get('responses', [])
            
            conv_id = conv_meta.get('id', self._generate_id(str(conv_meta)))
            
            # Skip if already processed
            if conv_id in self.conversations:
                continue
            
            conv = {
                'id': conv_id,
                'title': conv_meta.get('title', 'Untitled Conversation'),
                'messages': [],
                'created_at': conv_meta.get('create_time'),
                'updated_at': conv_meta.get('modify_time')
            }
            
            # Parse responses (messages)
            for response in responses:
                if not response or 'response' not in response:
                    continue
                
                msg = response['response']
                parsed = {
                    'id': msg.get('_id', self._generate_id(str(msg))),
                    'role': msg.get('sender', 'grok'),
                    'content': msg.get('message', ''),
                    'timestamp': msg.get('create_time'),
                    'metadata': {
                        'model': msg.get('model', ''),
                        'likes': 0,
                        'shares': 0,
                        'replies': 0
                    }
                }
                conv['messages'].append(parsed)
            
            if conv['messages']:
                self.conversations[conv['id']] = conv
                conversations.append(conv)
        
        return conversations
    
    def _parse_results(self, results):
        """Parse results array"""
        return [self._parse_single(r) for r in results if r]
    
    def _parse_messages(self, messages):
        """Parse messages array - treat as single conversation"""
        conv = {
            'id': self._generate_id('messages'),
            'title': 'Grok Conversation',
            'messages': [],
            'created_at': None,
            'updated_at': None
        }
        
        for msg in messages:
            parsed = self._parse_message(msg)
            if parsed:
                conv['messages'].append(parsed)
                if not conv['created_at']:
                    conv['created_at'] = parsed.get('timestamp')
                conv['updated_at'] = parsed.get('timestamp')
        
        if conv['messages']:
            self.conversations[conv['id']] = conv
            return [conv]
        return []
    
    def _parse_dict(self, data):
        """Parse a dictionary - check for nested structures"""
        # Check for nested arrays
        for key in ['conversations', 'results', 'messages', 'items', 'data']:
            if key in data and isinstance(data[key], list):
                return self.parse(data[key])
        
        # Single conversation object
        return [self._parse_single(data)] if data else []
    
    def _parse_single(self, item):
        """Parse a single conversation/item"""
        if not item:
            return None
        
        # Extract ID
        conv_id = item.get('id') or item.get('conversation_id') or self._generate_id(str(item))
        
        # Skip if already processed
        if conv_id in self.conversations:
            return self.conversations[conv_id]
        
        conv = {
            'id': conv_id,
            'title': self._extract_title(item),
            'messages': [],
            'created_at': None,
            'updated_at': None
        }
        
        # Extract messages
        messages = item.get('messages', []) or item.get('posts', []) or item.get('items', [])
        for msg in messages:
            parsed = self._parse_message(msg)
            if parsed:
                conv['messages'].append(parsed)
                if not conv['created_at']:
                    conv['created_at'] = parsed.get('timestamp')
                conv['updated_at'] = parsed.get('timestamp')
        
        if conv['messages']:
            self.conversations[conv['id']] = conv
            return conv
        return None
    
    def _parse_message(self, msg):
        """Parse a single message"""
        if not msg:
            return None
        
        return {
            'id': msg.get('id') or self._generate_id(str(msg)),
            'role': msg.get('role') or msg.get('author') or 'user',
            'content': msg.get('content') or msg.get('text') or msg.get('body') or '',
            'timestamp': msg.get('timestamp') or msg.get('created_at') or msg.get('date'),
            'metadata': {
                'likes': msg.get('likes', 0),
                'shares': msg.get('shares', 0),
                'replies': msg.get('replies', 0)
            }
        }
    
    def _extract_title(self, item):
        """Extract conversation title"""
        # Try various fields
        for field in ['title', 'name', 'subject', 'topic']:
            if field in item and item[field]:
                return item[field]
        
        # Generate from first message
        messages = item.get('messages', []) or item.get('posts', [])
        if messages:
            first_msg = messages[0] if isinstance(messages[0], str) else messages[0].get('content', '')
            if first_msg:
                return first_msg[:50] + '...' if len(first_msg) > 50 else first_msg
        
        return 'Untitled Conversation'
    
    def _generate_id(self, content):
        """Generate unique ID from content"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def get_conversation(self, conversation_id):
        """Get specific conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def search(self, query):
        """Search conversations for query"""
        query = query.lower()
        results = []
        
        for conv_id, conv in self.conversations.items():
            matches = []
            for msg in conv['messages']:
                if query in msg.get('content', '').lower():
                    matches.append({
                        'message_id': msg['id'],
                        'preview': msg['content'][:100],
                        'role': msg['role']
                    })
            
            if matches:
                results.append({
                    'conversation_id': conv_id,
                    'title': conv['title'],
                    'match_count': len(matches),
                    'matches': matches
                })
        
        return results
    
    def to_reddit_style(self, conversation_id):
        """Convert conversation to Reddit-style format"""
        conv = self.get_conversation(conversation_id)
        if not conv:
            return None
        
        return converter.to_reddit_style(conv)


# Import converter for method above
from core.converter import RedditConverter
converter = RedditConverter()
