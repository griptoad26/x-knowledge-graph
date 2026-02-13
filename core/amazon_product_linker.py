"""
Amazon Product Linker - X Knowledge Graph Addon
Detects product mentions in action items and generates Amazon search URLs.
"""

import re
from typing import Optional


# Product-related trigger words
PRODUCT_TRIGGERS = [
    'buy', 'purchase', 'get', 'need', 'want', 'shop', 'order',
    'looking for', 'searching for', 'find a', 'find an', 'get a', 'get an'
]

# Words to filter out when extracting product keywords
STOP_WORDS = frozenset([
    'a', 'an', 'the', 'my', 'for', 'to', 'with', 'on', 'new', 'need',
    'want', 'get', 'buy', 'purchase', 'looking', 'searching', 'find',
    'this', 'that', 'some', 'any', 'good', 'best', 'nice', 'great',
    'really', 'very', 'just', 'still', 'maybe', 'perhaps', 'probably',
    # Context words (what the product is for, not what it is)
    'computer', 'pc', 'home', 'office', 'room',
    'kitchen', 'bathroom', 'bedroom', 'living', 'car',
    'gym', 'workout', 'running', 'hiking', 'camping', 'travel',
    'today', 'tomorrow', 'week', 'month', 'soon', 'ASAP'
])

# Common product categories (for context-aware extraction)
PRODUCT_CATEGORIES = {
    'electronics': ['mouse', 'keyboard', 'monitor', 'laptop', 'phone', 'tablet', 'headphone', 'speaker', 'camera', 'charger', 'cable', 'adapter', 'coffee', 'coffee maker', 'printer', 'router', 'webcam', 'wallet', 'watch', 'earbuds', 'power bank'],
    'office': ['desk', 'chair', 'paper', 'pen', 'notebook', 'stapler', 'organizer', 'folder', 'binder'],
    'home': ['lamp', 'shelf', 'rug', 'curtain', 'pillow', 'blanket', 'towel', 'mirror', 'clock'],
    'kitchen': ['pot', 'pan', 'knife', 'spoon', 'fork', 'plate', 'bowl', 'cup', 'mug', 'blender', 'toaster'],
    'clothing': ['shirt', 'pants', 'jacket', 'shoes', 'socks', 'hat', 'scarf', 'gloves'],
    'fitness': ['weights', 'yoga', 'mat', 'band', 'bike', 'treadmill', 'dumbbell'],
    'books': ['book', 'novel', 'guide', 'manual', 'textbook', 'journal'],
}


class AmazonProductLinker:
    """Detects product mentions in actions and generates Amazon search URLs"""
    
    def __init__(self):
        # Pre-build regex pattern for detecting product triggers
        self.trigger_pattern = self._build_trigger_pattern()
        # All product category keywords for detection
        self.all_product_keywords = self._collect_all_keywords()
    
    def _build_trigger_pattern(self) -> re.Pattern:
        """Build regex pattern for product triggers"""
        trigger_escaped = [re.escape(t) for t in PRODUCT_TRIGGERS]
        pattern = r'(' + '|'.join(trigger_escaped) + r')'
        return re.compile(pattern, re.IGNORECASE)
    
    def _collect_all_keywords(self) -> set:
        """Collect all product keywords from categories"""
        keywords = set()
        for category_keywords in PRODUCT_CATEGORIES.values():
            keywords.update(category_keywords)
        return keywords
    
    def detect_product_mention(self, text: str) -> bool:
        """Check if action text mentions a product to buy/purchase"""
        text_lower = text.lower()
        
        # Check for product trigger words
        if self.trigger_pattern.search(text_lower):
            # Check if there's likely a product noun after
            match = self.trigger_pattern.search(text_lower)
            if match:
                remaining = text_lower[match.end():]
                if self._has_product_noun(remaining):
                    return True
        
        return False
    
    def _has_product_noun(self, text: str) -> bool:
        """Check if text contains likely product nouns"""
        text_lower = text.lower()
        
        # Check against known product categories
        for keyword in self.all_product_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def extract_product_keywords(self, text: str) -> Optional[str]:
        """Extract product keywords from action text for Amazon search"""
        text_lower = text.lower()
        
        # First try: find trigger word and extract what follows
        match = self.trigger_pattern.search(text_lower)
        if match:
            # Get text after the trigger
            after_trigger = text_lower[match.end():].strip()
            
            # Skip common words at the start
            words = after_trigger.split()
            filtered_words = []
            
            for word in words:
                # Remove punctuation
                clean_word = re.sub(r'[^\w]', '', word)
                if clean_word and clean_word.lower() not in STOP_WORDS:
                    filtered_words.append(clean_word.lower())
            
            # Get up to 4 meaningful words (product keywords)
            keywords = filtered_words[:4]
            
            if keywords:
                return '+'.join(keywords)
        
        # Fallback: extract any known product keywords from the text
        found_keywords = []
        words = re.findall(r'\b\w+\b', text_lower)
        for word in words:
            if word in self.all_product_keywords and word not in STOP_WORDS:
                found_keywords.append(word)
                if len(found_keywords) >= 4:
                    break
        
        if found_keywords:
            return '+'.join(found_keywords)
        
        return None
        
        return None
    
    def generate_amazon_url(self, text: str) -> Optional[str]:
        """Generate Amazon search URL from action text"""
        keywords = self.extract_product_keywords(text)
        
        if not keywords:
            return None
        
        return f"https://www.amazon.com/s?k={keywords}"
    
    def process_action_text(self, text: str) -> dict:
        """Process action text and return product link info"""
        return {
            'has_product': self.detect_product_mention(text),
            'keywords': self.extract_product_keywords(text),
            'amazon_link': self.generate_amazon_url(text)
        }


# Global instance for efficient reuse
_linker_instance = None


def get_linker() -> AmazonProductLinker:
    """Get or create the global AmazonProductLinker instance"""
    global _linker_instance
    if _linker_instance is None:
        _linker_instance = AmazonProductLinker()
    return _linker_instance


def get_amazon_link(text: str) -> Optional[str]:
    """Convenience function to get Amazon link from action text"""
    return get_linker().generate_amazon_url(text)


def extract_product_info(text: str) -> dict:
    """Convenience function to get all product info from action text"""
    return get_linker().process_action_text(text)


# Exact function signatures as requested
def detect_product_mentions(text: str) -> bool:
    """Check if text mentions a product to buy (alias for detect_product_mention)"""
    return get_linker().detect_product_mention(text)


def extract_product_keywords(text: str) -> list:
    """Extract product keywords from action text as a list"""
    result = get_linker().extract_product_keywords(text)
    return result.split('+') if result else []


def generate_amazon_url_from_keywords(keywords: list) -> str:
    """Generate Amazon search URL from a list of keywords"""
    if not keywords:
        return ""
    keyword_str = '+'.join(keywords)
    return f"https://www.amazon.com/s?k={keyword_str}"


def generate_amazon_url(text: str) -> str:
    """Generate Amazon search URL from action text - returns None if not product-related"""
    linker = get_linker()
    # Only generate URL if it's actually a product mention
    if not linker.detect_product_mention(text):
        return ""
    keywords = linker.extract_product_keywords(text)
    if not keywords:
        return ""
    return f"https://www.amazon.com/s?k={keywords}"
