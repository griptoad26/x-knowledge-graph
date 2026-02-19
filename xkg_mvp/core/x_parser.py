#!/usr/bin/env python3
"""
X Parser - Extract tweets and bookmarked content from X exports
Handles tweet.js format and bookmark exports
"""

import json
import os
import hashlib
from datetime import datetime


class XParser:
    """Parse X/Twitter data exports"""
    
    def __init__(self):
        self.tweets = {}
        self.bookmarks = []
        self.users = {}
    
    def parse(self, data):
        """
        Main entry point for parsing X data
        Handles tweet.js format and other X exports
        """
        if isinstance(data, dict):
            return self._parse_dict(data)
        elif isinstance(data, list):
            return self._parse_list(data)
        return []
    
    def _parse_dict(self, data):
        """Parse dictionary format"""
        # Check for tweet.js format (has 'tweets' key with array)
        if 'tweets' in data and isinstance(data['tweets'], list):
            return self._parse_tweets_array(data['tweets'])
        
        # Check for X export format
        if isinstance(data.get('__typename'), str):
            return self._parse_x_user(data)
        
        # Check for bookmarks
        if 'bookmarks' in data:
            return self._parse_bookmarks(data['bookmarks'])
        
        return []
    
    def _parse_list(self, items):
        """Parse list of tweets"""
        tweets = []
        for item in items:
            if isinstance(item, dict):
                tweet = self._parse_single_tweet(item)
                if tweet:
                    tweets.append(tweet)
        return tweets
    
    def _parse_tweets_array(self, tweets_array):
        """Parse array of tweets from tweet.js"""
        tweets = []
        for item in tweets_array:
            tweet = self._parse_single_tweet(item)
            if tweet:
                tweets.append(tweet)
                self.tweets[tweet['id']] = tweet
        return tweets
    
    def _parse_single_tweet(self, item):
        """Parse a single tweet"""
        if not item:
            return None
        
        tweet_id = item.get('id_str', item.get('id'))
        if not tweet_id:
            return None
        
        # Check if already parsed
        if tweet_id in self.tweets:
            return self.tweets[tweet_id]
        
        tweet = {
            'id': tweet_id,
            'content': self._extract_content(item),
            'timestamp': self._extract_timestamp(item),
            'username': item.get('user', {}).get('screen_name', 'unknown'),
            'display_name': item.get('user', {}).get('name', 'Unknown'),
            'likes': item.get('favorite_count', 0),
            'retweets': item.get('retweet_count', 0),
            'replies': item.get('reply_count', 0),
            'quotes': item.get('quote_count', 0),
            'source': 'X',
            'url': f"https://twitter.com/{item.get('user', {}).get('screen_name', '')}/status/{tweet_id}",
            'bookmarked': False,
            'in_reply_to': item.get('in_reply_to_status_id_str'),
            'retweeted_status': item.get('retweeted_status'),
            'quoted_status': item.get('quoted_status'),
            'entities': item.get('entities', {}),
            'extended_entities': item.get('extended_entities', {}),
            'created_at': item.get('created_at')
        }
        
        # Check for bookmark
        if item.get('bookmark'):
            tweet['bookmarked'] = True
            self.bookmarks.append(tweet)
        
        self.tweets[tweet_id] = tweet
        return tweet
    
    def _extract_content(self, item):
        """Extract tweet text content"""
        # Check for full_text (Twitter API format)
        if 'full_text' in item:
            return item['full_text']
        
        # Check for text
        if 'text' in item:
            return item['text']
        
        # Check for RT prefix
        if item.get('retweeted_status'):
            return self._extract_content(item['retweeted_status'])
        
        return ''
    
    def _extract_timestamp(self, item):
        """Extract tweet timestamp"""
        # Check for created_at string
        if 'created_at' in item:
            return item['created_at']
        
        # Check for timestamp_ms
        if 'timestamp_ms' in item:
            try:
                return datetime.fromtimestamp(int(item['timestamp_ms'])/1000).isoformat()
            except:
                pass
        
        return None
    
    def _parse_x_user(self, data):
        """Parse X user profile data"""
        if data.get('__typename') != 'User':
            return []
        
        user = {
            'id': data.get('rest_id', data.get('id')),
            'username': data.get('legacy', {}).get('screen_name', 'unknown'),
            'display_name': data.get('legacy', {}).get('name', 'Unknown'),
            'bio': data.get('legacy', {}).get('description', ''),
            'followers': data.get('legacy', {}).get('followers_count', 0),
            'following': data.get('legacy', {}).get('friends_count', 0),
            'tweets': data.get('legacy', {}).get('statuses_count', 0),
            'source': 'X Profile'
        }
        
        self.users[user['id']] = user
        return [user]
    
    def _parse_bookmarks(self, bookmarks_data):
        """Parse bookmarks data"""
        bookmarks = []
        
        if isinstance(bookmarks_data, list):
            for item in bookmarks_data:
                tweet = self._parse_single_tweet(item)
                if tweet:
                    tweet['bookmarked'] = True
                    bookmarks.append(tweet)
                    self.bookmarks.append(tweet)
        
        elif isinstance(bookmarks_data, dict):
            if 'bookmarks' in bookmarks_data:
                for item in bookmarks_data['bookmarks']:
                    tweet = self._parse_single_tweet(item)
                    if tweet:
                        tweet['bookmarked'] = True
                        bookmarks.append(tweet)
                        self.bookmarks.append(tweet)
        
        return bookmarks
    
    def get_tweet(self, tweet_id):
        """Get specific tweet by ID"""
        return self.tweets.get(tweet_id)
    
    def get_conversation(self, conversation_id):
        """Get conversation/tweet by ID"""
        # Try tweets first
        tweet = self.tweets.get(conversation_id)
        if tweet:
            return {
                'id': tweet['id'],
                'title': f"Tweet by @{tweet['username']}",
                'messages': [{
                    'id': tweet['id'],
                    'role': 'author',
                    'content': tweet['content'],
                    'timestamp': tweet['timestamp'],
                    'metadata': {
                        'likes': tweet['likes'],
                        'retweets': tweet['retweets'],
                        'replies': tweet['replies']
                    }
                }],
                'created_at': tweet['created_at'],
                'type': 'x_tweet'
            }
        
        # Try users
        user = self.users.get(conversation_id)
        if user:
            return {
                'id': user['id'],
                'title': f"X Profile: @{user['username']}",
                'messages': [],
                'created_at': None,
                'type': 'x_user'
            }
        
        return None
    
    def get_bookmarked_tweets(self):
        """Get all bookmarked tweets"""
        return self.bookmarks
    
    def search(self, query):
        """Search tweets"""
        query = query.lower()
        results = []
        
        for tweet_id, tweet in self.tweets.items():
            if query in tweet.get('content', '').lower():
                results.append({
                    'tweet_id': tweet_id,
                    'content': tweet['content'][:200],
                    'username': tweet['username'],
                    'likes': tweet['likes'],
                    'timestamp': tweet['timestamp'],
                    'bookmarked': tweet['bookmarked']
                })
        
        return results
    
    def to_reddit_style(self, conversation_id):
        """Convert tweet to Reddit-style format"""
        tweet = self.get_conversation(conversation_id)
        if not tweet:
            return None
        
        # Format as Reddit-style
        lines = [
            f"**{tweet['title']}**",
            "",
            f"_{tweet.get('messages', [{}])[0].get('content', '')}_",
            "",
            f"---",
            f"*Source: X (Twitter)*"
        ]
        
        return "\n".join(lines)
