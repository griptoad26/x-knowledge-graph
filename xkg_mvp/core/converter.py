#!/usr/bin/env python3
"""
Reddit Converter - Format conversations as Reddit-style content
"""

from datetime import datetime


class RedditConverter:
    """Convert conversations to Reddit-style markdown format"""
    
    ROLE_ICONS = {
        'user': '👤',
        'assistant': '🤖',
        'system': '⚙️',
        'grok': '🚀',
        'admin': '👑'
    }
    
    ROLE_LABELS = {
        'user': 'User',
        'assistant': 'Assistant',
        'system': 'System',
        'grok': 'Grok',
        'admin': 'Admin'
    }
    
    def __init__(self):
        pass
    
    def to_reddit_style(self, conversation, show_metadata=True):
        """
        Convert conversation to Reddit-style markdown
        
        Args:
            conversation: Dictionary with id, title, messages, timestamps
            show_metadata: Include vote/comment counts
            
        Returns:
            Reddit-style markdown string
        """
        lines = []
        
        # Header
        lines.append(f"# {conversation['title']}")
        lines.append("")
        lines.append(f"**Conversation ID:** `{conversation['id']}`")
        lines.append(f"**Messages:** {len(conversation['messages'])}")
        if conversation.get('created_at'):
            lines.append(f"**Created:** {conversation['created_at']}")
        lines.append("")
        
        # Divider
        lines.append("---")
        lines.append("")
        
        # Messages
        for i, msg in enumerate(conversation['messages']):
            lines.append(self._format_message(msg, i + 1, show_metadata))
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_message(self, msg, index, show_metadata=True):
        """Format single message in Reddit style"""
        role = msg.get('role', 'user').lower()
        icon = self.ROLE_ICONS.get(role, '💬')
        label = self.ROLE_LABELS.get(role, role.capitalize())
        
        lines = []
        
        # Message header (collapsed by default in some viewers)
        lines.append(f"### {icon} **{label}**")
        lines.append("")
        
        # Content
        content = msg.get('content', '')
        lines.append(content)
        lines.append("")
        
        # Metadata (Reddit-style footer)
        if show_metadata:
            meta = msg.get('metadata', {})
            likes = meta.get('likes', 0)
            shares = meta.get('shares', 0)
            replies = meta.get('replies', 0)
            
            if likes or shares or replies:
                meta_parts = []
                if likes:
                    meta_parts.append(f"⬆️ {likes}")
                if shares:
                    meta_parts.append(f"🔗 {shares}")
                if replies:
                    meta_parts.append(f"💬 {replies}")
                lines.append(f"^{' · '.join(meta_parts)}")
                lines.append("")
        
        # Message divider
        lines.append("---")
        
        return "\n".join(lines)
    
    def to_markdown(self, conversation):
        """
        Convert conversation to clean markdown (not Reddit style)
        
        Args:
            conversation: Dictionary with id, title, messages
            
        Returns:
            Clean markdown string
        """
        lines = []
        
        # Title
        lines.append(f"# {conversation['title']}")
        lines.append("")
        
        # Info
        lines.append(f"*Conversation ID: {conversation['id']}*")
        lines.append("")
        
        # Messages
        for msg in conversation['messages']:
            role = msg.get('role', 'user').capitalize()
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            lines.append(f"## {role}")
            if timestamp:
                lines.append(f"*[{timestamp}]*")
            lines.append("")
            lines.append(content)
            lines.append("")
        
        return "\n".join(lines)
    
    def to_html(self, conversation):
        """
        Convert conversation to HTML
        
        Args:
            conversation: Dictionary with id, title, messages
            
        Returns:
            HTML string
        """
        lines = []
        
        # HTML wrapper
        lines.append('<!DOCTYPE html>')
        lines.append('<html>')
        lines.append('<head>')
        lines.append(f'<title>{conversation["title"]}</title>')
        lines.append('<style>')
        lines.append('body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }')
        lines.append('.message { margin: 20px 0; padding: 15px; border-radius: 8px; }')
        lines.append('.user { background: #f0f0f0; }')
        lines.append('.assistant { background: #e8f4ea; }')
        lines.append('.role { font-weight: bold; margin-bottom: 5px; }')
        lines.append('.timestamp { color: #666; font-size: 0.9em; }')
        lines.append('.content { white-space: pre-wrap; }')
        lines.append('</style>')
        lines.append('</head>')
        lines.append('<body>')
        lines.append(f'<h1>{conversation["title"]}</h1>')
        lines.append(f'<p><em>ID: {conversation["id"]}</em></p>')
        
        for msg in conversation['messages']:
            role = msg.get('role', 'user').lower()
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            lines.append(f'<div class="message {role}">')
            lines.append(f'<div class="role">{role.capitalize()}</div>')
            if timestamp:
                lines.append(f'<div class="timestamp">[{timestamp}]</div>')
            lines.append(f'<div class="content">{content}</div>')
            lines.append('</div>')
        
        lines.append('</body>')
        lines.append('</html>')
        
        return "\n".join(lines)
    
    def to_json(self, conversation):
        """Return conversation as JSON string"""
        import json
        return json.dumps(conversation, indent=2)
    
    def format_timestamp(self, timestamp):
        """Format timestamp to readable date"""
        if not timestamp:
            return ""
        
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M')
            return str(timestamp)
        except:
            return str(timestamp)
    
    def to_bookmarks_markdown(self, tweets):
        """
        Convert bookmarked tweets to Reddit-style markdown
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            Markdown string with all bookmarks
        """
        lines = []
        
        # Header
        lines.append("# X Bookmarks Export")
        lines.append("")
        lines.append(f"*Total tweets: {len(tweets)}*")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Sort by timestamp (newest first)
        sorted_tweets = sorted(tweets, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        for i, tweet in enumerate(sorted_tweets, 1):
            lines.append(f"## {i}. @{tweet.get('username', 'unknown')}")
            lines.append("")
            
            # Content
            content = tweet.get('content', '')
            lines.append(content)
            lines.append("")
            
            # Metadata
            lines.append(f"❤️ {tweet.get('likes', 0)} · 🔄 {tweet.get('retweets', 0)} · 💬 {tweet.get('replies', 0)}")
            
            # Timestamp and URL
            ts = self.format_timestamp(tweet.get('timestamp', ''))
            if ts:
                lines.append(f"*{ts}*")
            
            url = tweet.get('url', '')
            if url:
                lines.append(f"[View on X]({url})")
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
