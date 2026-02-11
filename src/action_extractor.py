"""
Action item extraction from text content.
Identifies actionable items like todos, tasks, and follow-ups.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExtractedAction:
    """Represents an extracted action item"""
    text: str
    source_id: str
    source_type: str
    priority: str = "medium"
    topic: Optional[str] = None
    confidence: float = 0.5
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = f"action_{hash(self.text) % 1000000}"


class ActionExtractor:
    """
    Extracts action items from text content.
    
    Uses patterns and heuristics to identify:
    - Explicit TODOs: "TODO:", "todo:", "Action:"
    - Imperative statements: "Need to X", "Must X", "Should X"
    - Time-bound items: "by Friday", "due [date]"
    - Assignations: "@action [name]", "#todo"
    """
    
    def __init__(self, config=None):
        # Action detection patterns (ordered by specificity)
        self.explicit_patterns = [
            (r'\b(todo|to-do|to do)\s*[:\-]?\s*(.+?)(?:\.|,|$)', "explicit_todo", 0.9),
            (r'\b(action|task)\s*[:\-]?\s*(.+?)(?:\.|,|$)', "explicit_action", 0.9),
            (r'\b@action\s+(.+?)(?:\.|,|$)', "assigned_action", 0.85),
            (r'\b#todo\s+(.+?)(?:\.|,|$)', "hashtag_todo", 0.8),
        ]
        
        # Imperative patterns (lower confidence, more false positives)
        self.imperative_patterns = [
            (r'\b(need to|must|should|have to|gotta)\s+(.+?)(?:\.|,|$)', "imperative", 0.6),
            (r'\b(remember to|don\'t forget to|don\'t forget)\s+(.+?)(?:\.|,|$)', "reminder", 0.7),
            (r'\b(follow up|follow-up)\s+(?:on\s+)?(.+?)(?:\.|,|$)', "follow_up", 0.65),
            (r'\b(start|finish|complete|do|make|create|build|write|send|buy|get|set up)\s+(.+?)(?:\.|,|$)', "verb_start", 0.5),
        ]
        
        # Priority indicators
        self.priority_indicators = {
            "urgent": [r'\burgent\b', r'\basap\b', r'\bimmediately\b', r'\bnow\b', r'\btonight\b', r'\btoday\b'],
            "high": [r'\bimportant\b', r'\bpriority\b', r'\bcritical\b', r'\bsoon\b', r'\bthis week\b'],
            "low": [r'\beventually\b', r'\bsometime\b', r'\bmaybe\b', r'\bwhen possible\b']
        }
        
        # Deadline patterns
        self.deadline_patterns = [
            (r'\bby\s+(\w+\s+\d{1,2}|\d{1,2}/\d{1,2}|\w+\s+\d{4})', "deadline"),
            (r'\bdue\s+(\w+\s+\d{1,2}|\d{1,2}/\d{1,2})', "deadline"),
            (r'\bbefore\s+(\w+)', "deadline"),
        ]
        
        self.config = config
    
    def extract_all_actions(self, content_items: List[Dict]) -> List[ExtractedAction]:
        """Extract actions from a list of content items"""
        actions = []
        
        for item in content_items:
            text = item.get("text", "")
            source_id = str(item.get("id", ""))
            source_type = item.get("type", "tweet")
            
            extracted = self.extract_from_text(text, source_id, source_type)
            actions.extend(extracted)
        
        return actions
    
    def extract_from_text(self, text: str, source_id: str, source_type: str) -> List[ExtractedAction]:
        """Extract action items from a single text"""
        if not text:
            return []
        
        actions = []
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            action = self._analyze_sentence(sentence)
            if action:
                action.source_id = source_id
                action.source_type = source_type
                actions.append(action)
        
        return actions
    
    def _analyze_sentence(self, sentence: str) -> Optional[ExtractedAction]:
        """Analyze a single sentence for action items"""
        sentence = sentence.strip()
        if len(sentence) < 5:
            return None
        
        # Check explicit patterns first (higher confidence)
        for pattern, ptype, base_confidence in self.explicit_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                action_text = match.group(2).strip() if len(match.groups()) > 1 else match.group(1).strip()
                
                return ExtractedAction(
                    text=sentence,  # Keep full sentence for context
                    source_id="",
                    source_type="",
                    priority=self._detect_priority(sentence),
                    confidence=base_confidence
                )
        
        # Check imperative patterns
        for pattern, ptype, base_confidence in self.imperative_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return ExtractedAction(
                    text=sentence,
                    source_id="",
                    source_type="",
                    priority=self._detect_priority(sentence),
                    confidence=base_confidence
                )
        
        return None
    
    def _detect_priority(self, text: str) -> str:
        """Detect priority level from text"""
        text_lower = text.lower()
        
        for priority, patterns in self.priority_indicators.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return priority
        
        return "medium"
    
    def _detect_deadline(self, text: str) -> Optional[str]:
        """Extract deadline from text"""
        for pattern, ptype in self.deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Split on common sentence terminators
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def extract_actions_bulk(self, texts: List[str], source_prefix: str = "doc") -> List[ExtractedAction]:
        """Extract actions from multiple texts"""
        actions = []
        
        for i, text in enumerate(texts):
            extracted = self.extract_from_text(text, f"{source_prefix}_{i}", "document")
            actions.extend(extracted)
        
        return actions
    
    def categorize_actions(self, actions: List[ExtractedAction]) -> Dict[str, List[ExtractedAction]]:
        """Categorize actions by priority or other criteria"""
        categorized = {
            "urgent": [],
            "high": [],
            "medium": [],
            "low": [],
            "completed": []
        }
        
        for action in actions:
            if action.priority in categorized:
                categorized[action.priority].append(action)
            else:
                categorized["medium"].append(action)
        
        return categorized
