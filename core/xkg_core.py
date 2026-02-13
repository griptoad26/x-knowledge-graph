"""
X Knowledge Graph v0.4.6 - Core Engine
Parses X exports, builds conversation trees, extracts actions, links topics.
Adds Amazon product linking for action items and Dark Mode theming.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

try:
    from .todoist_exporter import TodoistExporter, export_actions_to_todoist
except ImportError:
    # Fallback if todoist_exporter not yet created
    TodoistExporter = None
    export_actions_to_todoist = None

# Import Amazon product linker
from .amazon_product_linker import AmazonProductLinker


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
class ActionItem:
    id: str
    text: str
    source_tweet_id: str
    topic: str
    priority: str  # urgent, high, medium, low
    status: str = "pending"  # pending, active, complete
    depends_on: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    amazon_link: Optional[str] = None  # Amazon search URL for product-related actions

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'text': self.text,
            'source_tweet_id': self.source_tweet_id,
            'topic': self.topic,
            'priority': self.priority,
            'status': self.status,
            'depends_on': self.depends_on,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'amazon_link': self.amazon_link
        }


@dataclass
class Topic:
    name: str
    keywords: List[str]
    tweet_ids: Set[str] = field(default_factory=set)
    action_ids: Set[str] = field(default_factory=set)
    related_topics: Set[str] = field(default_factory=set)


@dataclass
class Conversation:
    id: str
    root_tweet_id: str
    tweet_ids: List[str] = field(default_factory=list)
    participants: Set[str] = field(default_factory=set)
    topics: Set[str] = field(default_factory=set)
    action_ids: Set[str] = field(default_factory=set)


# ==================== GROK EXPORT PARSER ====================

class GrokExportParser:
    """Parse Grok export data files (conversations/posts)"""
    
    def __init__(self):
        self.posts: Dict[str, Dict] = {}
        self.conversations: Dict[str, Dict] = {}
    
    def find_all_json_files(self, directory: str) -> List[str]:
        """Recursively find all JSON files in directory tree"""
        json_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        return json_files
    
    def detect_export(self, export_path: str) -> List[str]:
        """Detect all JSON files in Grok export folder (recursive)"""
        export_path = Path(export_path)
        
        # Find all JSON files recursively
        json_files = self.find_all_json_files(str(export_path))
        
        # Filter for likely Grok data files
        grok_indicators = ['grok', 'conversation', 'post', 'message', 'chat', 'ai']
        grok_files = []
        
        for filepath in json_files:
            filename = os.path.basename(filepath).lower()
            # Check if filename contains any grok indicator
            if any(indicator in filename for indicator in grok_indicators):
                grok_files.append(filepath)
        
        # If no specific files found, include all JSON files
        if not grok_files:
            grok_files = json_files
        
        return grok_files
    
    def parse_export(self, export_path: str) -> Dict:
        """Parse Grok export folder - recursively finds and merges all JSON files"""
        result = {
            'posts': [],
            'conversations': [],
            'stats': {}
        }
        
        # Find all JSON files recursively
        json_files = self.detect_export(export_path)
        
        if not json_files:
            return {'error': 'No JSON files found in Grok export'}
        
        print(f"🔍 Found {len(json_files)} JSON files in Grok export")
        
        all_items = []
        
        for filepath in json_files:
            print(f"📄 Processing: {filepath}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Handle JS-wrapped JSON (like Twitter exports)
                content = re.sub(r'^window\.YTD\.\w+\.part\d*\s*=\s*', '', content)
                content = content.strip()
                
                # Try JSON parsing
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    # Try extracting JSON from text
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                    else:
                        print(f"⚠️ No valid JSON in: {filepath}")
                        continue
                
                # Normalize to list
                if isinstance(data, dict):
                    if 'posts' in data:
                        data = data['posts']
                    elif 'conversations' in data:
                        data = data['conversations']
                    elif 'messages' in data:
                        data = data['messages']
                    elif 'data' in data:
                        data = data['data']
                    elif 'items' in data:
                        data = data['items']
                    else:
                        data = [data]
                elif not isinstance(data, list):
                    data = [data]
                
                # Add items from this file
                if isinstance(data, list):
                    all_items.extend(data)
                    print(f"✅ Loaded {len(data)} items from {os.path.basename(filepath)}")
                else:
                    all_items.append(data)
                    
            except Exception as e:
                print(f"❌ Error reading {filepath}: {e}")
                continue
        
        # Deduplicate by ID
        seen_ids = set()
        unique_items = []
        for item in all_items:
            item_id = item.get('id') or item.get('post_id') or item.get('conversation_id') or item.get('message_id')
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_items.append(item)
        
        # Parse all unique items
        self.posts = {}
        for item in unique_items:
            post_data = self._normalize_post(item)
            post_id = post_data.get('id', str(len(self.posts)))
            self.posts[post_id] = post_data
        
        result['posts'] = list(self.posts.values())
        result['stats'] = {
            'total_files': len(json_files),
            'total_posts': len(self.posts),
            'unique_items': len(unique_items),
            'conversations': len(self.conversations)
        }
        
        print(f"✅ Total: {len(self.posts)} unique posts from {len(json_files)} files")
        
        return result
    
    def _normalize_post(self, item: Dict) -> Dict:
        """Normalize Grok post data to common format"""
        return {
            'id': item.get('id', item.get('post_id', '')),
            'text': item.get('text', item.get('content', item.get('message', ''))),
            'created_at': item.get('created_at', item.get('timestamp', item.get('date', ''))),
            'author_id': item.get('author_id', item.get('user_id', item.get('author', {}).get('id', '') if isinstance(item.get('author'), dict) else '')),
            'conversation_id': item.get('conversation_id', item.get('thread_id', '')),
            'in_reply_to_id': item.get('in_reply_to_id', item.get('reply_to', '')),
            'metrics': {
                'likes': item.get('metrics', {}).get('likes', item.get('likes', item.get('like_count', 0))),
                'shares': item.get('metrics', {}).get('shares', item.get('shares', item.get('share_count', 0))),
                'replies': item.get('metrics', {}).get('replies', item.get('replies', item.get('reply_count', 0))),
            },
            'entities': item.get('entities', item.get('mentions', [])),
            'source': 'grok'
        }


# ==================== X EXPORT PARSER ====================

class XExportParser:
    """Parse X export data files"""
    
    ACTION_PATTERNS = [
        r'\b(todo|to-do|TODO)\b',
        r'\b(need to|needs to)\b',
        r'\b(should|must|have to)\b',
        r'\b(going to|plan to)\b',
        r'\b(action item|action point)\b',
        r'\b(follow up|follow-up)\b',
        r'\b(remember to|don\'t forget)\b',
        r'\b(asap|urgent|important)\b',
        r'\b(deadline|due by)\b',
        r'\b(task|tasks)\b',
    ]
    
    URGENT_PATTERNS = [
        r'\basap\b',
        r'\burgent\b',
        r'\bimportant\b',
        r'\bcritical\b',
        r'\bdeadline\b',
        r'\bnow\b',
        r'\btoday\b',
    ]
    
    def __init__(self):
        self.tweets: Dict[str, Tweet] = {}
        self.likes: Dict[str, Dict] = {}
        self.replies: Dict[str, Dict] = {}
        self.conversations: Dict[str, Conversation] = {}
        
    def parse_export(self, export_path: str) -> Dict:
        """Parse X export folder"""
        result = {
            'tweets': [],
            'likes': [],
            'replies': [],
            'stats': {}
        }
        
        data_paths = [
            os.path.join(export_path, 'data', 'data'),
            os.path.join(export_path, 'data'),
            os.path.join(export_path),
        ]
        
        data_path = None
        for path in data_paths:
            if os.path.exists(path):
                data_path = path
                break
        
        if not data_path:
            return {'error': 'No data folder found'}
        
        tweet_file = self._find_file(data_path, ['tweet.js', 'tweets.js'])
        if tweet_file:
            self.tweets = self._parse_tweet_file(tweet_file)
            result['tweets'] = list(self.tweets.values())
        
        like_file = self._find_file(data_path, ['like.js', 'likes.js'])
        if like_file:
            self.likes = self._parse_like_file(like_file)
            result['likes'] = list(self.likes.values())
        
        reply_file = self._find_file(data_path, ['reply.js', 'replies.js'])
        if reply_file:
            self.replies = self._parse_reply_file(reply_file)
            result['replies'] = list(self.replies.values())
        
        self._build_conversations()
        
        result['stats'] = {
            'total_tweets': len(self.tweets),
            'total_likes': len(self.likes),
            'total_replies': len(self.replies),
            'conversations': len(self.conversations)
        }
        
        return result
    
    def _find_file(self, path: str, names: List[str]) -> Optional[str]:
        for name in names:
            filepath = os.path.join(path, name)
            if os.path.exists(filepath):
                return filepath
        return None
    
    def _parse_tweet_file(self, filepath: str) -> Dict[str, Tweet]:
        tweets = {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(r'^window\.YTD\.\w+\.part\d*\s*=\s*', '', content)
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return tweets
        
        for item in data:
            try:
                if 'tweet' in item:
                    tweet_data = item['tweet']
                else:
                    tweet_data = item
                
                tweet = Tweet(
                    id=tweet_data.get('id', ''),
                    text=tweet_data.get('text', ''),
                    created_at=tweet_data.get('created_at', ''),
                    author_id=tweet_data.get('user', {}).get('id', '') if isinstance(tweet_data.get('user'), dict) else '',
                    in_reply_to_status_id=tweet_data.get('in_reply_to_status_id'),
                    conversation_id=tweet_data.get('conversation_id'),
                    entities=tweet_data.get('entities', {}),
                    metrics=tweet_data.get('metrics', {})
                )
                tweets[tweet.id] = tweet
            except Exception:
                continue
        
        return tweets
    
    def _parse_like_file(self, filepath: str) -> Dict[str, Dict]:
        likes = {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(r'^window\.YTD\.\w+\.part\d*\s*=\s*', '', content)
        
        try:
            data = json.loads(content)
            for item in data:
                like_data = item.get('like', item)
                likes[like_data.get('tweetId', '')] = like_data
        except json.JSONDecodeError:
            pass
        
        return likes
    
    def _parse_reply_file(self, filepath: str) -> Dict[str, Dict]:
        replies = {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(r'^window\.YTD\.\w+\.part\d*\s*=\s*', '', content)
        
        try:
            data = json.loads(content)
            for item in data:
                reply_data = item.get('reply', item)
                replies[reply_data.get('tweetId', '')] = reply_data
        except json.JSONDecodeError:
            pass
        
        return replies
    
    def _build_conversations(self):
        conversation_map = defaultdict(lambda: {
            'tweets': [],
            'participants': set()
        })
        
        for tweet_id, tweet in self.tweets.items():
            if tweet.conversation_id:
                conversation_map[tweet.conversation_id]['tweets'].append(tweet_id)
                conversation_map[tweet.conversation_id]['participants'].add(tweet.author_id)
        
        for reply_id, reply in self.replies.items():
            conv_id = reply.get('conversationId')
            if conv_id:
                conversation_map[conv_id]['tweets'].append(reply_id)
                conversation_map[conv_id]['participants'].add(reply.get('authorId', ''))
        
        for conv_id, data in conversation_map.items():
            tweet_ids = data['tweets']
            root_id = tweet_ids[0] if tweet_ids else None
            
            conversation = Conversation(
                id=conv_id,
                root_tweet_id=root_id,
                tweet_ids=tweet_ids,
                participants=data['participants']
            )
            self.conversations[conv_id] = conversation


# ==================== ACTION EXTRACTOR ====================

class ActionExtractor:
    """Extract action items from tweets"""
    
    ACTION_PATTERNS = [
        (r'(?:TODO|TO-DO|Task):\s*(.+?)(?:\.|$)', 'high'),
        (r'(?:need to|needs to|have to|should)\s+(.+?)(?:\.|$)', 'medium'),
        (r'(?:going to|plan to|will)\s+(.+?)(?:\.|$)', 'low'),
        (r'(?:remember to|don\'t forget to?)\s+(.+?)(?:\.|$)', 'medium'),
        (r'(?:follow up|follow-up)\s+(?:on|with)?\s*(.+?)(?:\.|$)', 'high'),
        (r'(?:action item|action point):\s*(.+?)(?:\.|$)', 'high'),
        (r'\b(asap|urgent|critical)\b.*?(?:\.|$)', 'urgent'),
        (r'(?:deadline|due)\s+(?:by|on)?\s*(.+?)(?:\.|$)', 'urgent'),
        (r'(?:make sure to?|ensure|verify|check)\s+(.+?)(?:\.|$)', 'medium'),
        # Product purchase patterns
        (r'(?:buy|purchase|order|get)\s+(?:a|an|the|new|some)?\s+(.+?)(?:\.|$)', 'medium'),
        (r'(?:looking for|searching for|need a|need an)\s+(.+?)(?:\.|$)', 'medium'),
    ]
    
    def __init__(self):
        self.amazon_linker = AmazonProductLinker()
    
    def extract_actions(self, tweets: List[Tweet]) -> List[ActionItem]:
        actions = []
        
        for tweet in tweets:
            extracted = self._extract_from_text(tweet.text, tweet.id)
            for action in extracted:
                actions.append(action)
        
        return actions
    
    def _extract_from_text(self, text: str, source_id: str) -> List[ActionItem]:
        actions = []
        
        for pattern, priority in self.ACTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and len(match.strip()) > 3:
                    action_text = match.strip()[:200]
                    action = ActionItem(
                        id=f"action_{len(actions)}",
                        text=action_text,
                        source_tweet_id=source_id,
                        topic=self._extract_topic(text),
                        priority=priority,
                        amazon_link=self._extract_amazon_link(text, action_text)
                    )
                    actions.append(action)
        
        return actions
    
    def _extract_amazon_link(self, original_text: str, action_text: str = None) -> Optional[str]:
        """Extract Amazon search URL from action text if it mentions a product"""
        # Use original text for better keyword extraction (has trigger words)
        text_to_use = original_text if action_text is None else original_text
        
        # First try with full detection (requires trigger word)
        url = self.amazon_linker.generate_amazon_url(text_to_use)
        if url:
            return url
        
        # Fallback: if it has product keywords, generate URL anyway
        keywords = self.amazon_linker.extract_product_keywords(text_to_use)
        if keywords:
            return f"https://www.amazon.com/s?k={keywords}"
        
        return None
    
    def _extract_topic(self, text: str) -> str:
        text_lower = text.lower()
        
        topics = {
            'work': ['project', 'deadline', 'meeting', 'client', 'work'],
            'personal': ['family', 'home', 'weekend', 'birthday'],
            'development': ['code', 'build', 'deploy', 'api', 'github'],
            'learning': ['read', 'study', 'learn', 'course', 'tutorial'],
            'finance': ['money', 'budget', 'invest', 'payment', 'invoice'],
            'health': ['gym', 'work', 'medout', 'doctoricine', 'exercise'],
            'social': ['call', 'message', 'email', 'coffee', 'lunch'],
        }
        
        for topic, keywords in topics.items():
            if any(kw in text_lower for kw in keywords):
                return topic
        
        return 'general'


# ==================== TOPIC LINKER ====================

class TopicLinker:
    """Link tweets and actions by topic"""
    
    TOPIC_KEYWORDS = {
        'technology': ['python', 'code', 'api', 'github', 'software', 'ai', 'ml'],
        'business': ['business', 'revenue', 'client', 'project', 'deadline', 'meeting'],
        'personal': ['family', 'home', 'weekend', 'birthday', 'vacation'],
        'finance': ['money', 'budget', 'invest', 'payment', 'invoice', 'crypto'],
        'health': ['gym', 'workout', 'doctor', 'health', 'exercise', 'food'],
        'social': ['twitter', 'x', 'post', 'share', 'community', 'friend'],
        'learning': ['course', 'book', 'learn', 'study', 'tutorial', 'read'],
    }
    
    def __init__(self):
        self.topics: Dict[str, Topic] = {}
    
    def link_content(self, tweets: List[Tweet], actions: List[ActionItem]) -> Dict[str, Topic]:
        """Link tweets and actions to topics - returns Topic objects"""
        
        # Create topics
        for topic_name in self.TOPIC_KEYWORDS:
            self.topics[topic_name] = Topic(
                name=topic_name,
                keywords=self.TOPIC_KEYWORDS[topic_name]
            )
        
        # Add general topic
        self.topics['general'] = Topic(
            name='general',
            keywords=[]
        )
        
        # Link tweets to topics
        for tweet in tweets:
            topic = self._classify_text(tweet.text)
            if topic in self.topics:
                self.topics[topic].tweet_ids.add(tweet.id)
        
        # Link actions to topics
        for action in actions:
            if action.topic in self.topics:
                self.topics[action.topic].action_ids.add(action.id)
        
        # Link related topics
        self._link_related_topics()
        
        return self.topics
    
    def get_topics_dict(self) -> Dict:
        """Return topics as JSON-serializable dicts"""
        return {name: {
            'name': topic.name,
            'keywords': topic.keywords,
            'tweet_count': len(topic.tweet_ids),
            'action_count': len(topic.action_ids),
            'related': list(topic.related_topics)
        } for name, topic in self.topics.items()}
    
    def _classify_text(self, text: str) -> str:
        text_lower = text.lower()
        
        best_topic = 'general'
        best_score = 0
        
        for topic_name, keywords in self.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_topic = topic_name
        
        return best_topic
    
    def _link_related_topics(self):
        for topic1_name, topic1 in self.topics.items():
            for topic2_name, topic2 in self.topics.items():
                if topic1_name != topic2_name:
                    if topic1.tweet_ids & topic2.tweet_ids:
                        topic1.related_topics.add(topic2_name)
                        topic2.related_topics.add(topic1_name)


# ==================== TASK FLOW MANAGER ====================

class TaskFlowManager:
    """Manage task flows and dependencies"""
    
    def __init__(self):
        self.flows: Dict[str, List[str]] = {}
        self.action_status: Dict[str, str] = {}
    
    def build_flows(self, actions: List[ActionItem], topics: Dict[str, Topic]) -> Dict:
        """Build task flows for each topic"""
        
        topic_actions = defaultdict(list)
        for action in actions:
            topic_actions[action.topic].append(action)
        
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        
        flows = {}
        for topic, topic_action_list in topic_actions.items():
            sorted_actions = sorted(
                topic_action_list,
                key=lambda a: (priority_order.get(a.priority, 3), a.created_at)
            )
            
            flows[topic] = [a.id for a in sorted_actions]
            
            for action in sorted_actions:
                self.action_status[action.id] = action.status
        
        self.flows = dict(flows)
        
        return {
            'flows': self.flows,
            'action_status': self.action_status
        }
    
    def get_next_action(self, topic: str) -> Optional[ActionItem]:
        if topic not in self.flows:
            return None
        
        for action_id in self.flows[topic]:
            if self.action_status.get(action_id, 'pending') == 'pending':
                return action_id
        return None
    
    def complete_action(self, action_id: str) -> Dict:
        self.action_status[action_id] = 'complete'
        
        for topic, action_ids in self.flows.items():
            if action_id in action_ids:
                idx = action_ids.index(action_id)
                for next_id in action_ids[idx+1:]:
                    if self.action_status.get(next_id, 'pending') == 'pending':
                        return {
                            'completed': action_id,
                            'next': next_id,
                            'topic': topic,
                            'all_complete': False
                        }
                return {
                    'completed': action_id,
                    'next': None,
                    'topic': topic,
                    'all_complete': True
                }
        
        return {'error': 'Action not found'}
    
    def get_progress(self) -> Dict:
        progress = {}
        for topic, action_ids in self.flows.items():
            total = len(action_ids)
            complete = sum(1 for aid in action_ids if self.action_status.get(aid) == 'complete')
            progress[topic] = {
                'total': total,
                'complete': complete,
                'percent': int(complete / total * 100) if total > 0 else 100
            }
        return progress


# ==================== KNOWLEDGE GRAPH ====================

class KnowledgeGraph:
    """Main knowledge graph class"""
    
    def __init__(self):
        self.x_parser = XExportParser()
        self.grok_parser = GrokExportParser()
        self.extractor = ActionExtractor()
        self.linker = TopicLinker()
        self.flow_manager = TaskFlowManager()
        
        self.tweets: Dict[str, Tweet] = {}
        self.grok_posts: Dict[str, Dict] = {}
        self.actions: List[ActionItem] = []
        self.topics: Dict[str, Topic] = {}
        self.conversations: Dict[str, Conversation] = {}
    
    def build_from_export(self, export_path: str, export_type: str = 'x') -> Dict:
        """Build knowledge graph from X or Grok export"""
        
        if export_type == 'grok':
            return self._build_from_grok(export_path)
        else:
            return self._build_from_x(export_path)
    
    def _build_from_x(self, export_path: str) -> Dict:
        """Build knowledge graph from X export"""
        
        print(f"Parsing X export from: {export_path}")
        parse_result = self.x_parser.parse_export(export_path)
        
        if 'error' in parse_result:
            return parse_result
        
        self.tweets = self.x_parser.tweets
        self.conversations = self.x_parser.conversations
        
        print(f"Extracting actions from {len(self.tweets)} tweets...")
        self.actions = self.extractor.extract_actions(list(self.tweets.values()))
        
        print(f"Linking topics...")
        self.topics = self.linker.link_content(
            list(self.tweets.values()),
            self.actions
        )
        
        print(f"Building task flows...")
        flow_result = self.flow_manager.build_flows(self.actions, self.topics)
        
        # Return with JSON-serializable topic dict
        return {
            'stats': {
                'total_tweets': len(self.tweets),
                'total_likes': len(self.x_parser.likes),
                'total_replies': len(self.x_parser.replies),
                'total_conversations': len(self.conversations),
                'total_actions': len(self.actions),
                'topics_count': len(self.topics),
                'source': 'x'
            },
            'tweets': {tid: {
                'id': t.id,
                'text': t.text[:100],
                'is_reply': t.is_reply,
                'conversation_id': t.conversation_id
            } for tid, t in self.tweets.items()},
            'actions': [a.to_dict() for a in self.actions],
            'topics': self.linker.get_topics_dict(),
            'flows': flow_result['flows'],
            'progress': self.flow_manager.get_progress()
        }
    
    def _build_from_grok(self, export_path: str) -> Dict:
        """Build knowledge graph from Grok export"""
        
        print(f"Parsing Grok export from: {export_path}")
        parse_result = self.grok_parser.parse_export(export_path)
        
        if 'error' in parse_result:
            return parse_result
        
        self.grok_posts = self.grok_parser.posts
        
        # Convert Grok posts to Tweet-like objects for unified processing
        grok_tweets = []
        for post_id, post in self.grok_posts.items():
            tweet = Tweet(
                id=post_id,
                text=post.get('text', ''),
                created_at=post.get('created_at', ''),
                author_id=post.get('author_id', ''),
                in_reply_to_status_id=post.get('in_reply_to_id'),
                conversation_id=post.get('conversation_id'),
                entities={'hashtags': [], 'mentions': post.get('entities', [])},
                metrics=post.get('metrics', {})
            )
            grok_tweets.append(tweet)
        
        print(f"Extracting actions from {len(grok_tweets)} Grok posts...")
        self.actions = self.extractor.extract_actions(grok_tweets)
        
        print(f"Linking topics...")
        self.topics = self.linker.link_content(grok_tweets, self.actions)
        
        print(f"Building task flows...")
        flow_result = self.flow_manager.build_flows(self.actions, self.topics)
        
        # Return with JSON-serializable data
        return {
            'stats': {
                'total_tweets': len(grok_tweets),
                'total_likes': 0,
                'total_replies': 0,
                'total_conversations': 0,
                'total_actions': len(self.actions),
                'topics_count': len(self.topics),
                'source': 'grok'
            },
            'tweets': {tid: {
                'id': t.id,
                'text': t.text[:100],
                'is_reply': t.is_reply,
                'conversation_id': t.conversation_id
            } for tid, t in {t.id: t for t in grok_tweets}.items()},
            'actions': [a.to_dict() for a in self.actions],
            'topics': self.linker.get_topics_dict(),
            'flows': flow_result['flows'],
            'progress': self.flow_manager.get_progress()
        }
    
    def build_from_both(self, x_path: str, grok_path: str) -> Dict:
        """Build knowledge graph from both X and Grok exports"""
        
        # Build X graph
        x_result = self._build_from_x(x_path)
        if 'error' not in x_result:
            self.tweets = self.x_parser.tweets
            self.conversations = self.x_parser.conversations
        
        # Build Grok graph and merge
        grok_result = self._build_from_grok(grok_path)
        if 'error' not in grok_result:
            self.grok_posts = self.grok_parser.posts
        
        # Merge actions
        all_actions = []
        if 'actions' in x_result:
            all_actions.extend(x_result['actions'])
        if 'actions' in grok_result:
            all_actions.extend(grok_result['actions'])
        
        # Rebuild topics with all content
        all_tweets = list(self.tweets.values())
        grok_tweets = []
        for post_id, post in self.grok_posts.items():
            tweet = Tweet(
                id=post_id,
                text=post.get('text', ''),
                created_at=post.get('created_at', ''),
                author_id=post.get('author_id', ''),
                in_reply_to_status_id=post.get('in_reply_to_id'),
                conversation_id=post.get('conversation_id'),
                entities={'hashtags': [], 'mentions': post.get('entities', [])},
                metrics=post.get('metrics', {})
            )
            grok_tweets.append(tweet)
        all_tweets.extend(grok_tweets)
        
        # Relink topics with all content
        self.topics = self.linker.link_content(all_tweets, self.actions)
        
        print(f"Building task flows...")
        flow_result = self.flow_manager.build_flows(self.actions, self.topics)
        
        return {
            'stats': {
                'total_tweets': len(self.tweets) + len(self.grok_posts),
                'total_likes': len(self.x_parser.likes),
                'total_replies': len(self.x_parser.replies),
                'total_conversations': len(self.conversations),
                'total_actions': len(self.actions),
                'topics_count': len(self.topics),
                'source': 'both'
            },
            'tweets': {tid: {
                'id': t.id,
                'text': t.text[:100],
                'is_reply': t.is_reply,
                'conversation_id': t.conversation_id
            } for tid, t in {t.id: t for t in all_tweets}.items()},
            'actions': [a.to_dict() for a in self.actions],
            'topics': self.linker.get_topics_dict(),
            'flows': flow_result['flows'],
            'progress': self.flow_manager.get_progress()
        }
    
    def get_action_by_id(self, action_id: str) -> Optional[ActionItem]:
        for action in self.actions:
            if action.id == action_id:
                return action
        return None
    
    def export_for_d3(self) -> Dict:
        """Export for D3.js visualization"""
        nodes = []
        edges = []
        
        # Tweet nodes (X)
        for tid, tweet in self.tweets.items():
            nodes.append({
                'id': f"tweet_{tid}",
                'type': 'tweet',
                'label': tweet.text[:30] + '...' if len(tweet.text) > 30 else tweet.text,
                'topic': self._get_tweet_topic(tid)
            })
        
        # Grok post nodes
        for post_id, post in self.grok_posts.items():
            nodes.append({
                'id': f"grok_{post_id}",
                'type': 'grok',
                'label': post.get('text', '')[:30] + '...' if len(post.get('text', '')) > 30 else post.get('text', ''),
                'text': post.get('text', ''),
                'topic': self._get_tweet_topic(post_id)
            })
        
        # Action nodes
        for action in self.actions:
            nodes.append({
                'id': action.id,
                'type': 'action',
                'label': action.text[:30],
                'priority': action.priority,
                'status': action.status
            })
        
        # Topic nodes
        for topic_name, topic in self.topics.items():
            nodes.append({
                'id': f"topic_{topic_name}",
                'type': 'topic',
                'label': topic_name.upper()
            })
        
        # Tweet -> Reply edges (X)
        for tid, tweet in self.tweets.items():
            if tweet.in_reply_to_status_id:
                edges.append({
                    'source': f"tweet_{tid}",
                    'target': f"tweet_{tweet.in_reply_to_status_id}",
                    'type': 'reply_to'
                })
        
        # Grok -> Reply edges
        for post_id, post in self.grok_posts.items():
            if post.get('in_reply_to_id'):
                edges.append({
                    'source': f"grok_{post_id}",
                    'target': f"grok_{post.get('in_reply_to_id')}",
                    'type': 'reply_to'
                })
        
        # Tweet -> Topic edges
        for tid, tweet in self.tweets.items():
            topic = self._get_tweet_topic(tid)
            if topic:
                edges.append({
                    'source': f"tweet_{tid}",
                    'target': f"topic_{topic}",
                    'type': 'belongs_to'
                })
        
        # Grok -> Topic edges
        for post_id in self.grok_posts:
            topic = self._get_tweet_topic(post_id)
            if topic:
                edges.append({
                    'source': f"grok_{post_id}",
                    'target': f"topic_{topic}",
                    'type': 'belongs_to'
                })
        
        # Action -> Topic edges
        for action in self.actions:
            edges.append({
                'source': action.id,
                'target': f"topic_{action.topic}",
                'type': 'action_in'
            })
        
        return {'nodes': nodes, 'edges': edges}
    
    def _get_tweet_topic(self, tweet_id: str) -> Optional[str]:
        """Get topic for a tweet"""
        for topic_name, topic in self.topics.items():
            if tweet_id in topic.tweet_ids:
                return topic_name
        return None
    
    # ==================== TODOIST EXPORT ====================
    
    def export_to_todoist(
        self,
        api_token: Optional[str] = None,
        use_mock: bool = True,
        priority_filter: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict:
        """
        Export action items to Todoist
        
        Args:
            api_token: Todoist API token (defaults to TODOIST_API_TOKEN env var)
            use_mock: If True, use mock API for testing (default: True)
            priority_filter: List of priorities to export (e.g., ['urgent', 'high'])
            date_from: Export actions created on/after this date (ISO format)
            date_to: Export actions created on/before this date (ISO format)
            
        Returns:
            Dict with:
                - success_count: Number of successfully exported tasks
                - failed_count: Number of failed exports
                - task_ids: List of created Todoist task IDs
                - errors: List of error details for failed items
        """
        if not self.actions:
            return {
                'success_count': 0,
                'failed_count': 0,
                'total': 0,
                'task_ids': [],
                'errors': [{'error': 'No actions to export'}]
            }
        
        exporter = TodoistExporter(api_token=api_token, use_mock=use_mock)
        
        result = exporter.export_actions(
            actions=self.actions,
            priority_filter=priority_filter,
            date_from=date_from,
            date_to=date_to
        )
        
        return result
    
    def get_actions_by_priority(self, priority: str) -> List[ActionItem]:
        """
        Get actions filtered by priority level
        
        Args:
            priority: Priority level ('urgent', 'high', 'medium', 'low')
            
        Returns:
            List of ActionItem objects with matching priority
        """
        priority = priority.lower()
        return [a for a in self.actions if a.priority.lower() == priority]
    
    def get_actions_by_date_range(
        self,
        date_from: str,
        date_to: str
    ) -> List[ActionItem]:
        """
        Get actions within a date range
        
        Args:
            date_from: Start date (ISO format)
            date_to: End date (ISO format)
            
        Returns:
            List of ActionItem objects within the date range
        """
        return [
            a for a in self.actions
            if date_from <= a.created_at <= date_to
        ]
