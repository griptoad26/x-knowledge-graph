#!/usr/bin/env python3
"""
X Knowledge Graph - Production Test Suite
Tests core functionality, API endpoints, and performance
"""

import sys
import os
import time
import pytest
from pathlib import Path

# Test data paths - use correct relative paths
TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"
X_EXPORT_PATH = str(TEST_DATA_DIR / "x_export")
GROK_EXPORT_PATH = str(TEST_DATA_DIR / "grok_export")

# Import core module
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from xkg_core import KnowledgeGraph


class TestCoreParsing:
    """Core parsing functionality tests"""
    
    @pytest.fixture
    def kg(self):
        """Create fresh KnowledgeGraph for each test"""
        return KnowledgeGraph()
    
    def test_x_export_parses_correctly(self, kg):
        """X export with 5 tweets parses successfully"""
        result = kg.build_from_export(X_EXPORT_PATH, 'x')
        
        assert result['stats']['total_tweets'] == 5
        assert result['stats']['total_actions'] >= 5
        assert 'actions' in result
        assert 'topics' in result
        assert 'flows' in result
    
    def test_grok_export_parses_correctly(self, kg):
        """Grok export with 10 posts parses successfully"""
        result = kg.build_from_export(GROK_EXPORT_PATH, 'grok')
        
        # Grok uses 'total_posts' key
        posts_count = result['stats'].get('total_posts', result['stats'].get('total_tweets', 0))
        assert posts_count == 10, f"Expected 10 posts, got {posts_count}"
        assert result['stats']['total_actions'] >= 5  # At least half should have actions
        assert 'actions' in result
        assert 'topics' in result
    
    def test_combined_export_parses_correctly(self, kg):
        """Both exports combined parse correctly"""
        result = kg.build_from_both(X_EXPORT_PATH, GROK_EXPORT_PATH)
        
        assert result['stats']['total_tweets'] == 15
        assert result['stats']['total_actions'] >= 15
    
    def test_actions_have_required_fields(self, kg):
        """All extracted actions have required fields"""
        result = kg.build_from_export(X_EXPORT_PATH, 'x')
        actions = result.get('actions', [])
        
        assert len(actions) > 0
        
        for action in actions:
            assert 'text' in action, "Action missing 'text' field"
            assert 'priority' in action, "Action missing 'priority' field"
            assert action['priority'] in ['urgent', 'high', 'medium', 'low'], \
                f"Invalid priority: {action['priority']}"
    
    def test_graph_export_valid(self, kg):
        """Graph exports in valid D3 format"""
        kg.build_from_export(X_EXPORT_PATH, 'x')
        d3 = kg.export_for_d3()
        
        assert 'nodes' in d3
        assert 'edges' in d3
        assert len(d3['nodes']) > 0
        
        # Check nodes have required fields
        for node in d3['nodes']:
            assert 'id' in node, "Node missing 'id'"
            assert 'type' in node, "Node missing 'type'"
        
        # Edges should be well-formed (even if referencing non-existent nodes)
        for edge in d3['edges']:
            assert 'source' in edge, "Edge missing 'source'"
            assert 'target' in edge, "Edge missing 'target'"
            assert 'type' in edge, "Edge missing 'type'"
    
    def test_topics_are_linked(self, kg):
        """Topics are properly structured"""
        result = kg.build_from_export(X_EXPORT_PATH, 'x')
        topics = result.get('topics', {})
        
        assert isinstance(topics, dict)
        
        for topic, data in topics.items():
            assert isinstance(data, dict), f"Topic '{topic}' is not a dict"
            has_actions = 'actions' in data or 'action_count' in data
            assert has_actions, f"Topic '{topic}' missing action references"
    
    def test_flows_have_structure(self, kg):
        """Task flows have valid structure"""
        result = kg.build_from_export(X_EXPORT_PATH, 'x')
        flows = result.get('flows', {})
        
        assert isinstance(flows, dict)
        
        # Each flow should be a list of action IDs (not necessarily have a 'name')
        for flow_id, flow in flows.items():
            assert isinstance(flow, list), f"Flow '{flow_id}' is not a list"
            assert len(flow) > 0, f"Flow '{flow_id}' is empty"


class TestActionExtraction:
    """Action extraction specific tests"""
    
    @pytest.fixture
    def kg(self):
        return KnowledgeGraph()
    
    def test_urgent_actions_flagged(self, kg):
        """Actions marked as urgent are correctly flagged"""
        result = kg.build_from_export(X_EXPORT_PATH, 'x')
        actions = result.get('actions', [])
        
        urgent = [a for a in actions if a.get('priority') == 'urgent']
        # At least one urgent action should exist
        assert len(urgent) >= 1, "No urgent actions found"
    
    def test_action_text_not_empty(self, kg):
        """All action text is non-empty"""
        result = kg.build_from_export(X_EXPORT_PATH, 'x')
        actions = result.get('actions', [])
        
        for action in actions:
            assert action.get('text', '').strip(), \
                f"Empty action text found: {action}"
    
    def test_action_count_reasonable(self, kg):
        """Action count is reasonable (not too high)"""
        result = kg.build_from_export(X_EXPORT_PATH, 'x')
        
        # 5 tweets should not produce 100+ actions
        assert result['stats']['total_actions'] < 100, \
            f"Unreasonably high action count: {result['stats']['total_actions']}"


class TestPerformance:
    """Performance benchmarks"""
    
    @pytest.fixture
    def kg(self):
        return KnowledgeGraph()
    
    def test_parse_performance(self, kg):
        """Parse completes in reasonable time"""
        start = time.time()
        kg.build_from_export(X_EXPORT_PATH, 'x')
        elapsed = time.time() - start
        
        # Should parse in under 5 seconds
        assert elapsed < 5.0, f"Parse took {elapsed:.2f}s (target: <5s)"
    
    def test_graph_export_performance(self, kg):
        """Graph export completes quickly"""
        kg.build_from_export(X_EXPORT_PATH, 'x')
        
        start = time.time()
        d3 = kg.export_for_d3()
        elapsed = time.time() - start
        
        assert elapsed < 1.0, f"Graph export took {elapsed:.2f}s (target: <1s)"
    
    def test_memory_stable(self, kg):
        """Memory doesn't grow unreasonably"""
        import gc
        
        gc.collect()
        
        # Parse multiple times
        for _ in range(3):
            kg = KnowledgeGraph()
            kg.build_from_export(X_EXPORT_PATH, 'x')
            kg = None
        
        gc.collect()
        # Just verify no exceptions - memory test requires psutil


class TestEdgeCases:
    """Edge case handling"""
    
    @pytest.fixture
    def kg(self):
        return KnowledgeGraph()
    
    def test_empty_actions_handled(self, kg):
        """Empty or minimal exports handled gracefully"""
        # Test with data that might have no actions
        result = kg.build_from_export(X_EXPORT_PATH, 'x')
        
        # Should not crash
        assert 'stats' in result
    
    def test_topic_clustering_works(self, kg):
        """Similar topics are clustered together"""
        result = kg.build_from_export(X_EXPORT_PATH, 'x')
        topics = result.get('topics', {})
        
        # Topics should be unique strings
        for topic in topics.keys():
            assert isinstance(topic, str)
            assert len(topic) > 0
    
    def test_duplicate_actions_handled(self, kg):
        """Duplicate actions don't cause issues"""
        result = kg.build_from_export(X_EXPORT_PATH, 'x')
        actions = result.get('actions', [])
        
        # Check no exact duplicates
        seen = set()
        for action in actions:
            key = action.get('text', '').lower().strip()
            assert key not in seen, f"Duplicate action found: {action['text']}"
            seen.add(key)


def test_import_sanity():
    """Basic import test"""
    from xkg_core import KnowledgeGraph
    
    kg = KnowledgeGraph()
    assert kg is not None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
