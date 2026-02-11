"""
Knowledge Graph builder using NetworkX.
Creates a graph representation of X data with nodes for tweets, users, topics, and actions.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import sqlite3
import json
import uuid

import networkx as nx


class KnowledgeGraph:
    """
    Graph representation of X data.
    
    Node types:
    - tweet: Original tweets and replies
    - like: Liked tweets
    - retweet: Retweeted content
    - action: Action items extracted from content
    - topic: Topic clusters
    - grok: Grok conversation messages
    
    Edge types:
    - reply: Parent-child tweet relationship
    - like: User -> liked tweet
    - retweet: User retweet -> original tweet
    - contains_action: Tweet contains action item
    - similar: Content similarity above threshold
    - belongs_to: Content belongs to topic
    - related_to_grok: Content related to Grok conversation
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_counter = 0
        
        # Track special nodes
        self.user_id = "self"  # Will be set from data
        
    def add_tweets(self, tweets: List[Dict]):
        """Add tweet nodes to the graph"""
        for tweet in tweets:
            node_id = str(tweet.get("id", self._next_id()))
            
            self.graph.add_node(
                node_id,
                type="tweet",
                text=tweet.get("text", ""),
                timestamp=tweet.get("created_at"),
                user_id=tweet.get("user", {}).get("id"),
                in_reply_to=tweet.get("in_reply_to_status_id"),
                conversation_id=tweet.get("conversation_id"),
                entities=tweet.get("entities", {}),
                status="active"
            )
            
            # Add reply edge if this is a reply
            if tweet.get("in_reply_to_status_id"):
                parent_id = str(tweet["in_reply_to_status_id"])
                if parent_id in self.graph:
                    self.graph.add_edge(
                        parent_id, node_id,
                        relation="reply",
                        timestamp=tweet.get("created_at")
                    )
    
    def add_likes(self, likes: List[Dict]):
        """Add liked tweet nodes and like edges"""
        for like in likes:
            node_id = str(like.get("id", self._next_id()))
            
            self.graph.add_node(
                node_id,
                type="like",
                text=like.get("text", ""),
                timestamp=like.get("created_at"),
                user_id=like.get("user", {}).get("id"),
                original_author=like.get("user", {}).get("screen_name"),
                status="active"
            )
            
            # Add like edge from user
            self.graph.add_edge(
                self.user_id, node_id,
                relation="liked",
                timestamp=like.get("created_at")
            )
    
    def add_retweets(self, retweets: List[Dict]):
        """Add retweet nodes and retweet edges"""
        for retweet in retweets:
            node_id = str(retweet.get("id", self._next_id()))
            original = retweet.get("retweeted_status", {})
            original_id = str(original.get("id", self._next_id()))
            
            # Add original tweet node if not exists
            if original_id not in self.graph:
                self.graph.add_node(
                    original_id,
                    type="retweeted_original",
                    text=original.get("full_text", ""),
                    timestamp=original.get("created_at"),
                    user_id=original.get("user", {}).get("id"),
                    original_author=original.get("user", {}).get("screen_name"),
                    status="active"
                )
            
            # Add retweet node
            self.graph.add_node(
                node_id,
                type="retweet",
                text=retweet.get("text", ""),
                timestamp=retweet.get("created_at"),
                user_id=retweet.get("user", {}).get("id"),
                status="active"
            )
            
            # Add retweet edge
            self.graph.add_edge(
                node_id, original_id,
                relation="retweet_of",
                timestamp=retweet.get("created_at")
            )
    
    def add_actions(self, actions: List[Dict]):
        """Add action item nodes with edges to source content"""
        for action in actions:
            action_id = action.get("id", f"action_{self._next_id()}")
            
            self.graph.add_node(
                action_id,
                type="action",
                text=action.get("text", ""),
                source_id=action.get("source_id"),
                source_type=action.get("source_type"),
                topic=action.get("topic"),
                priority=action.get("priority", "medium"),
                status=action.get("status", "pending"),
                confidence=action.get("confidence", 0.5),
                created_at=datetime.now().isoformat(),
                completed_at=None
            )
            
            # Link to source content
            source_id = action.get("source_id")
            if source_id and source_id in self.graph:
                self.graph.add_edge(
                    source_id, action_id,
                    relation="contains_action",
                    confidence=action.get("confidence", 0.5)
                )
    
    def add_topics(self, topics: List[Dict]):
        """Add topic cluster nodes"""
        for topic in topics:
            topic_id = topic.get("id", f"topic_{self._next_id()}")
            
            self.graph.add_node(
                topic_id,
                type="topic",
                name=topic.get("name", ""),
                keywords=topic.get("keywords", []),
                description=topic.get("description", ""),
                node_count=topic.get("node_count", 0),
                created_at=datetime.now().isoformat()
            )
            
            # Link content to topic
            for content_id in topic.get("content_ids", []):
                if content_id in self.graph:
                    self.graph.add_edge(
                        content_id, topic_id,
                        relation="belongs_to",
                        weight=topic.get("weight", 1.0)
                    )
    
    def add_grok_messages(self, messages: List[Dict]):
        """Add Grok conversation message nodes"""
        for msg in messages:
            msg_id = msg.get("id", f"grok_{self._next_id()}")
            
            self.graph.add_node(
                msg_id,
                type="grok",
                text=msg.get("text", ""),
                role=msg.get("role", "user"),
                timestamp=msg.get("timestamp"),
                conversation_id=msg.get("conversation_id"),
                status="active"
            )
    
    def build_conversation_trees(self, tweets: List[Dict]) -> Dict[str, List[str]]:
        """
        Build conversation trees from reply relationships.
        Returns dict mapping conversation_id -> list of tweet IDs in order.
        """
        conversations = defaultdict(list)
        
        # Group by conversation_id
        for tweet in tweets:
            conv_id = tweet.get("conversation_id", "no_conversation")
            conversations[conv_id].append(tweet.get("id"))
        
        return dict(conversations)
    
    def link_similar_content(self, threshold: float = 0.7):
        """
        Link content nodes with high similarity.
        This is a placeholder - actual implementation uses embeddings.
        """
        # In production, compute embeddings and add similarity edges
        # For now, this is handled by the topic_modeler
        pass
    
    def link_grok_to_x(self, threshold: float = 0.7):
        """Link Grok messages to related X content"""
        # Find grok nodes and X nodes, compute similarity, add edges
        grok_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "grok"]
        x_nodes = [n for n, d in self.graph.nodes(data=True) 
                   if d.get("type") in ["tweet", "like", "retweet"]]
        
        # Placeholder: In production, use embeddings for similarity
        # For now, link by keyword matching
        for grok_id in grok_nodes:
            grok_text = self.graph.nodes[grok_id].get("text", "").lower()
            
            for x_id in x_nodes:
                x_text = self.graph.nodes[x_id].get("text", "").lower()
                
                # Simple keyword overlap
                grok_words = set(grok_text.split())
                x_words = set(x_text.split())
                overlap = grok_words & x_words
                
                if len(overlap) >= 3:  # At least 3 common words
                    self.graph.add_edge(
                        grok_id, x_id,
                        relation="related_to_grok",
                        weight=len(overlap) / len(grok_words | x_words)
                    )
    
    def get_pending_actions(self, topic: Optional[str] = None) -> List[Dict]:
        """Get all pending action items, optionally filtered by topic"""
        actions = []
        
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == "action" and data.get("status") == "pending":
                if topic is None or data.get("topic") == topic:
                    actions.append({
                        "id": node_id,
                        "text": data.get("text"),
                        "topic": data.get("topic"),
                        "priority": data.get("priority"),
                        "source_id": data.get("source_id"),
                        "confidence": data.get("confidence")
                    })
        
        # Sort by priority and confidence
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        actions.sort(key=lambda x: (
            priority_order.get(x.get("priority"), 4),
            -x.get("confidence", 0)
        ))
        
        return actions
    
    def get_actions_by_topic(self) -> Dict[str, List[Dict]]:
        """Group actions by topic"""
        grouped = defaultdict(list)
        
        for action in self.get_pending_actions():
            topic = action.get("topic") or "uncategorized"
            grouped[topic].append(action)
        
        return dict(grouped)
    
    def get_action_dependencies(self, action_id: str) -> List[str]:
        """Get actions that must complete before this action"""
        deps = []
        
        for predecessor in self.graph.predecessors(action_id):
            if self.graph.nodes[predecessor].get("type") == "action":
                deps.append(predecessor)
        
        return deps
    
    def get_action_dependents(self, action_id: str) -> List[str]:
        """Get actions that depend on this action completing"""
        dependents = []
        
        for successor in self.graph.successors(action_id):
            if self.graph.nodes[successor].get("type") == "action":
                dependents.append(successor)
        
        return dependents
    
    def mark_action_complete(self, action_id: str) -> bool:
        """Mark an action as complete"""
        if action_id in self.graph.nodes:
            self.graph.nodes[action_id]["status"] = "complete"
            self.graph.nodes[action_id]["completed_at"] = datetime.now().isoformat()
            return True
        return False
    
    def to_cytoscape_format(self) -> Dict:
        """Export graph in Cytoscape.js compatible format"""
        elements = {"nodes": [], "edges": []}
        
        for node_id, data in self.graph.nodes(data=True):
            elements["nodes"].append({
                "data": {
                    "id": node_id,
                    "label": data.get("text", "")[:50],
                    **data
                }
            })
        
        for source, target, data in self.graph.edges(data=True):
            elements["edges"].append({
                "data": {
                    "source": source,
                    "target": target,
                    **data
                }
            })
        
        return elements
    
    def save_to_db(self, path: str):
        """Persist graph to SQLite database"""
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                data TEXT,
                type TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source TEXT,
                target TEXT,
                relation TEXT,
                data TEXT,
                FOREIGN KEY (source) REFERENCES nodes(id),
                FOREIGN KEY (target) REFERENCES nodes(id)
            )
        """)
        
        # Clear existing
        cursor.execute("DELETE FROM nodes")
        cursor.execute("DELETE FROM edges")
        
        # Store nodes
        for node_id, data in self.graph.nodes(data=True):
            cursor.execute(
                "INSERT INTO nodes (id, data, type) VALUES (?, ?, ?)",
                (node_id, json.dumps(data), data.get("type", "unknown"))
            )
        
        # Store edges
        for source, target, data in self.graph.edges(data=True):
            cursor.execute(
                "INSERT INTO edges (source, target, relation, data) VALUES (?, ?, ?, ?)",
                (source, target, data.get("relation", "unknown"), json.dumps(data))
            )
        
        conn.commit()
        conn.close()
    
    def load_from_db(self, path: str):
        """Load graph from SQLite database"""
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Clear existing graph
        self.graph.clear()
        
        # Load nodes
        cursor.execute("SELECT id, data FROM nodes")
        for row in cursor.fetchall():
            node_id, data_json = row
            data = json.loads(data_json)
            self.graph.add_node(node_id, **data)
        
        # Load edges
        cursor.execute("SELECT source, target, relation, data FROM edges")
        for row in cursor.fetchall():
            source, target, relation, data_json = row
            data = json.loads(data_json)
            self.graph.add_edge(source, target, **data)
        
        conn.close()
    
    def _next_id(self) -> str:
        """Generate unique node ID"""
        self.node_counter += 1
        return f"node_{self.node_counter}"
    
    def get_stats(self) -> Dict:
        """Get graph statistics"""
        stats = {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": {},
            "edge_types": {}
        }
        
        for _, data in self.graph.nodes(data=True):
            node_type = data.get("type", "unknown")
            stats["node_types"][node_type] = stats["node_types"].get(node_type, 0) + 1
        
        for _, _, data in self.graph.edges(data=True):
            edge_type = data.get("relation", "unknown")
            stats["edge_types"][edge_type] = stats["edge_types"].get(edge_type, 0) + 1
        
        return stats
