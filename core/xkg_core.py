"""
X Knowledge Graph v0.4.33 - Core Engine
Parses X and Grok exports, builds conversation trees, extracts actions, links topics.
Supports ANY files in export folder - auto-detects format from content.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from collections import defaultdict

# Import Todoist exporter (try relative first, then absolute for bundled exe)
try:
    from .todoist_exporter import TodoistExporter, export_actions_to_todoist
except ImportError:
    try:
        from todoist_exporter import TodoistExporter, export_actions_to_todoist
    except ImportError:
        TodoistExporter = None
        export_actions_to_todoist = None

# Import Amazon product linker
try:
    from .amazon_product_linker import AmazonProductLinker
except ImportError:
    from amazon_product_linker import AmazonProductLinker


# ==================== DATA MODELS ====================

@dataclass
class Tweet:
    id: str
    text: str
    created_at: str
    author_id: str
    in_reply_to_status_id: Optional[str] = None
    conversation_id: Optional[str] = None
    referenced_tweets: List[str] = field(default_factory=list)
    entities: Dict = field(default_factory=dict)
    metrics: Dict = field(default_factory=dict)

    @property
    def is_reply(self) -> bool:
        return bool(self.in_reply_to_status_id)

    @property
    def is_retweet(self) -> bool:
        return self.text.startswith('RT @')


@dataclass
class GrokPost:
    id: str
    text: str
    created_at: str
    author_id: str
    conversation_id: Optional[str] = None
    in_reply_to_id: Optional[str] = None
    metrics: Dict = field(default_factory=dict)
    entities: List = field(default_factory=list)
    source: str = "grok"


@dataclass
class ActionItem:
    id: str
    text: str
    source_id: str
    source_type: str  # 'tweet' or 'grok'
    topic: str
    priority: str  # urgent, high, medium, low
    status: str = "pending"
    depends_on: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    amazon_link: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'text': self.text,
            'source_id': self.source_id,
            'source_type': self.source_type,
            'topic': self.topic,
            'priority': self.priority,
            'status': self.status,
            'depends_on': self.depends_on,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'amazon_link': self.amazon_link
        }


# ==================== FLEXIBLE FILE DISCOVERY ====================

def find_all_export_files(directory: str, extensions: List[str] = None) -> List[str]:
    """Find all files in directory matching extensions (recursive)"""
    if extensions is None:
        extensions = ['.json', '.js']
    
    files = []
    directory = Path(directory)
    
    if not directory.exists():
        return files
    
    # Always recurse into subdirectories
    for path in directory.rglob('*'):
        if path.is_file():
            # Match by extension OR by name containing any of the patterns
            suffix = path.suffix.lower()
            name_lower = path.name.lower()
            if suffix in extensions or any(ext in name_lower for ext in extensions):
                files.append(str(path))
    
    return sorted(set(files))  # Remove duplicates


def detect_export_format(filepath: str) -> str:
    """Auto-detect if file is X, Grok, or Production Log format based on content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for X export format (window.YTD)
        if 'window.YTD' in content or '.part0' in content:
            return 'x'
        
        # Try parsing as JSON
        try:
            data = json.loads(content)
            
            # Check for Grok format (list of posts with 'source': 'grok')
            if isinstance(data, list):
                if any(item.get('source') == 'grok' for item in data if isinstance(item, dict)):
                    return 'grok'
                # Check for common Grok fields
                first_item = data[0] if data else {}
                if any(field in first_item for field in ['author_id', 'conversation_id']):
                    if not any(field in str(first_item).lower() for field in ['retweet', 'in_reply_to']):
                        return 'grok'
            
            # Check for X format (dict with 'tweet' key)
            if isinstance(data, dict):
                if 'tweet' in data:
                    return 'x'
                if any(k for k in data.keys() if 'tweet' in k.lower()):
                    return 'x'
            
            # Check for tweets array format
            if isinstance(data, list):
                if any('created_at' in item and 'text' in item for item in data[:3]):
                    if any('user' in item or 'author' in item.lower() for item in data[:3]):
                        return 'x'
            
            # Check for Production Log format (server logs with timestamp/level/message)
            if isinstance(data, list):
                first_item = data[0] if data else {}
                # Check for log-like fields
                has_log_fields = (
                    ('timestamp' in first_item or 'time' in first_item or 'created_at' in first_item) and
                    ('level' in first_item or 'severity' in first_item or 'log_level' in first_item or 'level' in str(first_item).lower())
                )
                has_message = 'message' in first_item or 'msg' in first_item or 'log_message' in first_item
                has_service = 'service' in first_item or 'logger' in first_item or 'name' in first_item
                if has_log_fields or has_message:
                    return 'prodlog'
            
            # Check for prod-*.json filename pattern (production log files)
            filename = Path(filepath).name.lower()
            if filename.startswith('prod-') and filename.endswith('.json'):
                return 'prodlog'
        
        except json.JSONDecodeError:
            pass
        
        return 'unknown'
    
    except Exception:
        return 'unknown'


# ==================== FLEXIBLE X EXPORT PARSER ====================

class FlexibleXParser:
    """Parse X exports - handles ANY files in folder, auto-detects format"""
    
    def __init__(self):
        self.tweets: Dict[str, Tweet] = {}
        self.likes: Dict[str, Dict] = {}
        self.replies: Dict[str, Dict] = {}
        self.conversations: Dict[str, Dict] = {}
    
    def parse(self, export_path: str) -> Dict:
        """Parse X export folder - scans for all JSON/JS files"""
        result = {
            'tweets': [],
            'likes': [],
            'replies': [],
            'stats': {}
        }
        
        # Find all potential export files
        files = find_all_export_files(export_path, ['.json', '.js', 'tweet', 'like', 'reply'])
        
        if not files:
            return {'error': f'No export files found in {export_path}'}
        
        print(f"Found {len(files)} files in X export folder")
        
        for filepath in files:
            print(f"  Processing: {os.path.basename(filepath)}")
            format_type = detect_export_format(filepath)
            print(f"    Detected format: {format_type}")
            
            if format_type == 'x':
                self._parse_x_file(filepath)
            elif format_type == 'grok':
                # Skip grok files in X export
                print(f"    Skipping (Grok format)")
            else:
                # Try parsing as generic tweet format
                self._parse_generic_file(filepath)
        
        # Build conversations
        self._build_conversations()
        
        result['tweets'] = list(self.tweets.values())
        result['likes'] = list(self.likes.values())
        result['replies'] = list(self.replies.values())
        result['stats'] = {
            'total_tweets': len(self.tweets),
            'total_likes': len(self.likes),
            'total_replies': len(self.replies),
            'conversations': len(self.conversations)
        }
        
        return result
    
    def _parse_x_file(self, filepath: str):
        """Parse X export format (window.YTD or direct JSON)"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Handle window.YTD format
            if 'window.YTD' in content:
                content = re.sub(r'^window\.YTD\.\w+\.part\d*\s*=\s*', '', content)
            
            data = json.loads(content)
            
            # Handle list of tweets
            if isinstance(data, list):
                for item in data:
                    if 'tweet' in item:
                        tweet_data = item['tweet']
                    else:
                        tweet_data = item
                    tweet = self._create_tweet(tweet_data)
                    if tweet:
                        self.tweets[tweet.id] = tweet
            
            # Handle dict with tweets key
            elif isinstance(data, dict):
                if 'tweets' in data:
                    for item in data['tweets']:
                        tweet = self._create_tweet(item)
                        if tweet:
                            self.tweets[tweet.id] = tweet
                elif 'tweet' in data:
                    tweet = self._create_tweet(data['tweet'])
                    if tweet:
                        self.tweets[tweet.id] = tweet
        
        except Exception as e:
            print(f"    Error parsing {os.path.basename(filepath)}: {e}")
    
    def _parse_generic_file(self, filepath: str):
        """Parse generic JSON array of tweets"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    tweet = self._create_tweet(item)
                    if tweet:
                        self.tweets[tweet.id] = tweet
            elif isinstance(data, dict):
                tweet = self._create_tweet(data)
                if tweet:
                    self.tweets[tweet.id] = tweet
        
        except Exception as e:
            print(f"    Error parsing {os.path.basename(filepath)}: {e}")
    
    def _create_tweet(self, data: Dict) -> Optional[Tweet]:
        """Create Tweet object from parsed data"""
        try:
            tweet_id = str(data.get('id', data.get('id_str', '')))
            if not tweet_id:
                return None
            
            # Handle nested structure
            if 'tweet' in data:
                data = data['tweet']
            
            text = data.get('text', '')
            created_at = data.get('created_at', datetime.now().isoformat())
            
            # Handle user/author_id
            user = data.get('user', {})
            author_id = str(user.get('id', data.get('author_id', '')))
            
            # Handle metrics
            metrics = data.get('metrics', {})
            if not metrics and 'public_metrics' in data:
                metrics = data['public_metrics']
            
            # Handle entities
            entities = data.get('entities', {})
            
            return Tweet(
                id=tweet_id,
                text=text,
                created_at=created_at,
                author_id=author_id,
                in_reply_to_status_id=data.get('in_reply_to_status_id'),
                conversation_id=data.get('conversation_id'),
                entities=entities,
                metrics=metrics
            )
        
        except Exception:
            return None
    
    def _build_conversations(self):
        """Build conversation threads from replies"""
        for tweet_id, tweet in self.tweets.items():
            if tweet.in_reply_to_status_id:
                if tweet.in_reply_to_status_id not in self.conversations:
                    self.conversations[tweet.in_reply_to_status_id] = {
                        'root_id': tweet.in_reply_to_status_id,
                        'replies': []
                    }
                self.conversations[tweet.in_reply_to_status_id]['replies'].append(tweet_id)


# ==================== FLEXIBLE GROK EXPORT PARSER ====================

class FlexibleGrokParser:
    """Parse Grok exports - handles ANY files in folder, auto-detects format"""
    
    def __init__(self):
        self.posts: Dict[str, GrokPost] = {}
    
    def parse(self, export_path: str) -> Dict:
        """Parse Grok export folder - scans for all JSON files recursively"""
        result = {
            'posts': [],
            'stats': {}
        }
        
        # Find all potential export files (recursive)
        files = find_all_export_files(export_path, ['.json', '.js'])
        
        if not files:
            # Also try finding any files that might contain conversation/grok data
            files = find_all_export_files(export_path, ['*'])
        
        print(f"Scanning: {export_path}")
        print(f"Found {len(files)} files")
        
        # Show first few files for debugging
        for f in sorted(files)[:10]:
            print(f"  {f}")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")
        
        if not files:
            return {'error': f'No export files found in {export_path}'}
        
        for filepath in files:
            # Skip directories
            if os.path.isdir(filepath):
                continue
            print(f"  Processing: {os.path.basename(filepath)}")
            format_type = detect_export_format(filepath)
            print(f"    Detected format: {format_type}")
            
            if format_type == 'grok':
                self._parse_grok_file(filepath)
            elif format_type == 'prodlog':
                self._parse_prodlog_file(filepath)
            elif format_type == 'x':
                print(f"    Skipping (X format)")
            else:
                # Try as generic post format
                self._parse_generic_file(filepath)
        
        result['posts'] = list(self.posts.values())
        result['stats'] = {
            'total_posts': len(self.posts)
        }
        
        return result
    
    def _parse_grok_file(self, filepath: str):
        """Parse Grok export format"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    post = self._create_post(item)
                    if post:
                        self.posts[post.id] = post
            elif isinstance(data, dict):
                # Check for standard Grok formats
                if 'posts' in data:
                    for item in data['posts']:
                        post = self._create_post(item)
                        if post:
                            self.posts[post.id] = post
                elif 'conversations' in data:
                    for conv in data['conversations']:
                        if 'messages' in conv:
                            for item in conv['messages']:
                                post = self._create_post(item)
                                if post:
                                    self.posts[post.id] = post
                # Check for new Grok export format with results
                elif 'results' in data:
                    for item in data['results']:
                        post = self._create_post_from_grok_result(item)
                        if post:
                            self.posts[post.id] = post
                # Check for task-based format
                elif 'task' in data and 'results' in data.get('task', {}):
                    for item in data['task']['results']:
                        post = self._create_post_from_grok_result(item)
                        if post:
                            self.posts[post.id] = post
        
        except Exception as e:
            print(f"    Error parsing {os.path.basename(filepath)}: {e}")
    
    def _create_post_from_grok_result(self, data: Dict) -> Optional[GrokPost]:
        """Create GrokPost from new Grok result format (conversations with tasks)"""
        try:
            # Extract post info from task/conversation structure
            conversation_id = data.get('conversation_id', '')
            task_id = data.get('task_id', '')
            post_id = f"grok_{conversation_id}_{task_id}" if conversation_id and task_id else data.get('task_result_id', f"grok_{data.get('create_time', '')}")
            
            # Extract text from metadata.response_preview (may be HTML)
            metadata = data.get('metadata', {})
            response_preview = metadata.get('response_preview', '')
            
            # Strip HTML tags for clean text
            import re
            text = re.sub(r'<[^>]+>', '', response_preview).strip()
            if not text:
                text = data.get('title', '')
            
            created_at = data.get('create_time', data.get('update_time', datetime.now().isoformat()))
            status = data.get('status', '')
            error = data.get('error')
            
            # Only create post for successful results
            if error or status != 'Success':
                return None
            
            return GrokPost(
                id=post_id,
                text=text[:500] if text else '[No content]',  # Truncate long HTML
                created_at=created_at,
                author_id='grok',
                conversation_id=conversation_id,
                in_reply_to_id=None,
                metrics={'exec_time': metadata.get('exec_time', 0)},
                entities=[],
                source='grok'
            )
        
        except Exception:
            return None
    
    def _parse_prodlog_file(self, filepath: str):
        """Parse production log files as pseudo-posts"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                data = [data]
            
            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    continue
                
                # Extract log fields
                timestamp = item.get('timestamp', item.get('time', item.get('created_at', '')))
                level = item.get('level', item.get('severity', item.get('log_level', '')))
                message = item.get('message', item.get('msg', item.get('log_message', '')))
                service = item.get('service', item.get('logger', item.get('name', 'unknown')))
                
                # Skip empty messages
                if not message:
                    continue
                
                # Create a unique ID
                post_id = f"log_{Path(filepath).stem}_{idx}"
                
                # Use service + level as "author" for filtering later
                author_id = f"{service}_{level}"
                
                # Create the post
                post = GrokPost(
                    id=post_id,
                    text=message,
                    created_at=timestamp,
                    author_id=author_id,
                    conversation_id=None,
                    in_reply_to_id=None,
                    metrics={'level': level, 'service': service},
                    entities=[],
                    source='prodlog'
                )
                
                self.posts[post.id] = post
        
        except Exception as e:
            print(f"    Error parsing prodlog {os.path.basename(filepath)}: {e}")
    
    def _parse_generic_file(self, filepath: str):
        """Parse generic JSON as posts"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    post = self._create_post(item)
                    if post:
                        self.posts[post.id] = post
            elif isinstance(data, dict):
                if 'items' in data:
                    for item in data['items']:
                        post = self._create_post(item)
                        if post:
                            self.posts[post.id] = post
        
        except Exception as e:
            print(f"    Error parsing {os.path.basename(filepath)}: {e}")
    
    def _create_post(self, data: Dict) -> Optional[GrokPost]:
        """Create GrokPost from parsed data"""
        try:
            post_id = str(data.get('id', data.get('id_str', '')))
            if not post_id:
                return None
            
            text = data.get('text', data.get('content', ''))
            created_at = data.get('created_at', datetime.now().isoformat())
            author_id = str(data.get('author_id', data.get('user_id', '')))
            
            return GrokPost(
                id=post_id,
                text=text,
                created_at=created_at,
                author_id=author_id,
                conversation_id=data.get('conversation_id'),
                in_reply_to_id=data.get('in_reply_to_id'),
                metrics=data.get('metrics', data.get('stats', {})),
                entities=data.get('entities', []),
                source=data.get('source', 'grok')
            )
        
        except Exception:
            return None


# ==================== MAIN KNOWLEDGE GRAPH ====================

class KnowledgeGraph:
    """Main knowledge graph that combines X and Grok exports"""
    
    def __init__(self):
        self.tweets: Dict[str, Tweet] = {}
        self.posts: Dict[str, GrokPost] = {}
        self.actions: List[ActionItem] = []
        self.topics: Dict[str, Dict] = {}
        self.flows: Dict[str, List[str]] = {}
        
        # Priority keywords for action detection
        self.priority_keywords = {
            'urgent': ['urgent', 'asap', 'immediately', 'critical', 'emergency', 'blocking', 'priority 1'],
            'high': ['important', 'high priority', 'must', 'required', 'deadline', 'due'],
            'medium': ['should', 'need to', 'remember to', 'todo', 'fix', 'update', 'review'],
            'low': ['would be nice', 'consider', 'maybe', 'sometime', 'low priority']
        }
    
    def build_from_export(self, export_path: str, export_type: str = 'x') -> Dict:
        """Build knowledge graph from a single export"""
        
        if export_type == 'grok':
            parser = FlexibleGrokParser()
            result = parser.parse(export_path)
            self.posts = parser.posts
            tweets_count = 0
            posts_count = result['stats'].get('total_posts', 0)
        else:
            parser = FlexibleXParser()
            result = parser.parse(export_path)
            self.tweets = parser.tweets
            tweets_count = result['stats'].get('total_tweets', 0)
            posts_count = 0
        
        # Extract actions from parsed data
        self._extract_actions()
        
        # Cluster topics
        self._cluster_topics()
        
        # Build task flows
        self._build_flows()
        
        return {
            'stats': {
                'total_tweets': tweets_count,
                'total_posts': posts_count,
                'total_actions': len(self.actions),
                'topics_count': len(self.topics),
                'flows_count': len(self.flows)
            },
            'actions': [a.to_dict() for a in self.actions],
            'topics': self.topics,
            'flows': self.flows
        }
    
    def build_from_both(self, x_path: str, grok_path: str) -> Dict:
        """Build knowledge graph from both X and Grok exports"""
        
        print(f"\nParsing X export from: {x_path}")
        x_result = self.build_from_export(x_path, 'x')
        
        print(f"\nParsing Grok export from: {grok_path}")
        grok_result = self.build_from_export(grok_path, 'grok')
        
        # Combine stats
        combined_stats = {
            'total_tweets': x_result['stats']['total_tweets'] + grok_result['stats']['total_posts'],
            'total_posts': grok_result['stats']['total_posts'],
            'total_actions': len(self.actions),
            'topics_count': len(self.topics),
            'flows_count': len(self.flows)
        }
        
        return {
            'stats': combined_stats,
            'actions': [a.to_dict() for a in self.actions],
            'topics': self.topics,
            'flows': self.flows
        }
    
    def _extract_actions(self):
        """Extract action items from tweets and posts"""
        action_id = 0
        
        # Process tweets
        for tweet_id, tweet in self.tweets.items():
            actions = self._find_actions_in_text(tweet.text, tweet_id, 'tweet')
            for action_text, priority in actions:
                self.actions.append(ActionItem(
                    id=f'action_{action_id}',
                    text=action_text,
                    source_id=tweet_id,
                    source_type='tweet',
                    topic=self._extract_topic(action_text),
                    priority=priority
                ))
                action_id += 1
        
        # Process Grok posts
        for post_id, post in self.posts.items():
            actions = self._find_actions_in_text(post.text, post_id, 'grok')
            for action_text, priority in actions:
                self.actions.append(ActionItem(
                    id=f'action_{action_id}',
                    text=action_text,
                    source_id=post_id,
                    source_type='grok',
                    topic=self._extract_topic(action_text),
                    priority=priority
                ))
                action_id += 1
    
    def _find_actions_in_text(self, text: str, source_id: str, source_type: str) -> List[tuple]:
        """Find action items in text and their priorities"""
        actions = []
        text_lower = text.lower()
        
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Extract sentence containing the keyword
                    sentences = re.split(r'[.!?\n]', text)
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            sentence = sentence.strip()
                            if len(sentence) > 10 and len(sentence) < 500:
                                actions.append((sentence, priority))
                    break
        
        return actions
    
    def _extract_topic(self, text: str) -> str:
        """Extract topic from action text"""
        topic_keywords = {
            'api': ['api', 'endpoint', 'rest', 'json'],
            'database': ['database', 'db', 'sql', 'query'],
            'authentication': ['auth', 'login', 'password', 'oauth'],
            'performance': ['performance', 'speed', 'optimize', 'slow'],
            'documentation': ['docs', 'documentation', 'readme'],
            'testing': ['test', 'testing', 'qa', 'bug'],
            'ui': ['ui', 'interface', 'design', 'frontend'],
            'deployment': ['deploy', 'production', 'server', 'infrastructure'],
            'business': ['meeting', 'schedule', 'business', 'team'],
            'personal': ['buy', 'order', 'keyboard', 'office']
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return topic
        
        return 'general'
    
    def _cluster_topics(self):
        """Cluster actions by topic"""
        topic_actions = defaultdict(list)
        
        for action in self.actions:
            topic_actions[action.topic].append(action.id)
        
        self.topics = {
            topic: {
                'name': topic,
                'action_count': len(action_ids),
                'actions': action_ids,
                'keywords': [topic]  # Simplified - could be expanded
            }
            for topic, action_ids in topic_actions.items()
        }
    
    def _build_flows(self):
        """Build task flows (simplified - orders by priority)"""
        # Sort actions by priority
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        
        sorted_actions = sorted(
            self.actions,
            key=lambda a: (priority_order.get(a.priority, 3), a.created_at)
        )
        
        # Group by topic for flows
        topic_flows = defaultdict(list)
        for action in sorted_actions:
            topic_flows[action.topic].append(action.id)
        
        self.flows = dict(topic_flows)
    
    def export_for_d3(self) -> Dict:
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
                'topic': 'general'
            })
        
        # Grok post nodes
        for post_id, post in self.posts.items():
            nodes.append({
                'id': f'grok_{post_id}',
                'type': 'grok',
                'label': post.text[:50] + '...' if len(post.text) > 50 else post.text,
                'text': post.text,
                'topic': 'general'
            })
        
        # Action nodes
        for action in self.actions:
            source_id = f"{action.source_type[:1]}_{action.source_id}"
            nodes.append({
                'id': action.id,
                'type': 'action',
                'label': action.text[:40] + '...' if len(action.text) > 40 else action.text,
                'text': action.text,
                'priority': action.priority,
                'topic': action.topic
            })
            
            # Edge from source to action
            edges.append({
                'source': source_id,
                'target': action.id,
                'type': 'extracts'
            })
        
        # Topic nodes
        for topic, data in self.topics.items():
            nodes.append({
                'id': f'topic_{topic}',
                'type': 'topic',
                'label': topic.upper(),
                'topic': topic
            })
            
            # Edges from actions to topic
            for action_id in data.get('actions', []):
                edges.append({
                    'source': action_id,
                    'target': f'topic_{topic}',
                    'type': 'belongs_to'
                })
        
        return {'nodes': nodes, 'edges': edges}
