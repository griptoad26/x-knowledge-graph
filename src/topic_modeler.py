"""
Topic modeling for knowledge graph content.
Identifies themes and clusters similar content.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass
import re
import hashlib


@dataclass
class Topic:
    """Represents a topic cluster"""
    id: str
    name: str
    keywords: List[str]
    content_ids: List[str]
    description: str = ""
    weight: float = 1.0
    node_count: int = 0


class TopicModeler:
    """
    Simple topic modeling without heavy ML dependencies.
    
    Uses keyword extraction and clustering to group content by theme.
    In production, would use BERTopic or similar for embeddings.
    """
    
    def __init__(self, config=None):
        self.config = config
        
        # Common stop words to filter out
        self.stop_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'whose',
            'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also'
        ])
        
        # Keyword weights by position
        self.position_weights = {
            'title': 3.0,
            'hashtag': 2.5,
            'first_sentence': 1.5,
            'body': 1.0
        }
    
    def identify_topics(self, content_items: List[Dict]) -> List[Topic]:
        """
        Identify topics from a list of content items.
        
        Returns list of Topic objects with clustered content.
        """
        # Extract keywords from all content
        all_keywords = self._extract_all_keywords(content_items)
        
        # Find common themes
        themes = self._identify_themes(all_keywords)
        
        # Cluster content by theme
        topics = []
        for theme in themes:
            topic = self._create_topic(theme, content_items)
            if topic and topic.node_count >= 1:
                topics.append(topic)
        
        return topics
    
    def _extract_all_keywords(self, content_items: List[Dict]) -> Dict[str, float]:
        """Extract and weight keywords from all content"""
        keyword_weights = defaultdict(float)
        
        for item in content_items:
            text = item.get("text", "")
            keywords = self._extract_keywords(text)
            
            # Weight by content type
            content_type = item.get("type", "tweet")
            weight = self.position_weights.get(content_type, 1.0)
            
            for kw in keywords:
                keyword_weights[kw] += weight
        
        return dict(keyword_weights)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        if not text:
            return []
        
        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', text.lower())
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stop words and combine
        keywords = [w for w in words if w not in self.stop_words and len(w) > 2]
        
        # Add hashtags with slight boost
        keywords.extend([f"#{h}" for h in hashtags if h.lower() not in self.stop_words])
        
        return list(set(keywords))
    
    def _identify_themes(self, keyword_weights: Dict[str, float], min_weight: float = 2.0) -> List[Dict]:
        """Identify major themes from keyword weights"""
        # Sort by weight
        sorted_keywords = sorted(keyword_weights.items(), key=lambda x: -x[1])
        
        themes = []
        used_keywords = set()
        
        for keyword, weight in sorted_keywords:
            if weight < min_weight or keyword in used_keywords:
                continue
            
            # Start a new theme
            theme = {
                "name": keyword,
                "keywords": [keyword],
                "weight": weight,
                "related": []
            }
            
            # Find related keywords
            for other_kw, other_weight in sorted_keywords:
                if other_kw != keyword and other_kw not in used_keywords:
                    # Check for co-occurrence or similarity
                    if self._keywords_related(keyword, other_kw, keyword_weights):
                        theme["keywords"].append(other_kw)
                        theme["weight"] += other_weight * 0.5
                        used_keywords.add(other_kw)
            
            used_keywords.add(keyword)
            themes.append(theme)
        
        return themes
    
    def _keywords_related(self, kw1: str, kw2: str, keyword_weights: Dict[str, float]) -> bool:
        """Check if two keywords are related"""
        # Direct substring match
        if kw1 in kw2 or kw2 in kw1:
            return True
        
        # Hashtag vs non-hashtag
        if kw1.startswith("#") or kw2.startswith("#"):
            clean1 = kw1.lstrip("#")
            clean2 = kw2.lstrip("#")
            if clean1 == clean2:
                return True
        
        # Similar first letters (could be same topic)
        if kw1[0] == kw2[0]:
            return True
        
        return False
    
    def _create_topic(self, theme: Dict, content_items: List[Dict]) -> Optional[Topic]:
        """Create a Topic from theme data"""
        topic_name = theme["name"].replace("#", "").title()
        
        # Find content matching this topic
        content_ids = []
        for item in content_items:
            text = item.get("text", "").lower()
            item_keywords = self._extract_keywords(text)
            
            # Check if content matches topic keywords
            match_score = sum(1 for kw in theme["keywords"] if kw.lower() in text)
            
            if match_score > 0:
                content_ids.append(str(item.get("id", "")))
        
        if not content_ids:
            return None
        
        return Topic(
            id=f"topic_{hash(topic_name) % 10000}",
            name=topic_name,
            keywords=theme["keywords"],
            content_ids=content_ids,
            description=f"Topic cluster for {topic_name} and related terms",
            weight=theme["weight"],
            node_count=len(content_ids)
        )
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute simple text similarity (0-1)"""
        kw1 = set(self._extract_keywords(text1))
        kw2 = set(self._extract_keywords(text2))
        
        if not kw1 or not kw2:
            return 0.0
        
        intersection = kw1 & kw2
        union = kw1 | kw2
        
        return len(intersection) / len(union) if union else 0.0
    
    def cluster_by_similarity(self, texts: List[str], threshold: float = 0.3) -> List[List[int]]:
        """
        Cluster texts by similarity.
        Returns list of clusters, each as list of text indices.
        """
        if not texts:
            return []
        
        n = len(texts)
        visited = set()
        clusters = []
        
        for i in range(n):
            if i in visited:
                continue
            
            cluster = [i]
            visited.add(i)
            
            for j in range(i + 1, n):
                if j not in visited:
                    sim = self.compute_similarity(texts[i], texts[j])
                    if sim >= threshold:
                        cluster.append(j)
                        visited.add(j)
            
            if len(cluster) >= 1:
                clusters.append(cluster)
        
        return clusters
    
    def generate_topic_name(self, keywords: List[str]) -> str:
        """Generate a readable topic name from keywords"""
        if not keywords:
            return "General"
        
        # Take top 3 keywords
        top_kw = keywords[:3]
        
        # Clean and format
        cleaned = [kw.replace("#", "").title() for kw in top_kw]
        
        return " / ".join(cleaned)
