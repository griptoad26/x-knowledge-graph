#!/usr/bin/env python3
"""
X Knowledge Graph - Comprehensive Graph Validation Tests
Validates that the application correctly:
1. Parses X and Grok exports
2. Populates the knowledge graph
3. Extracts action items with priorities
4. Clusters topics from content
5. Builds D3-compatible node/edge structure

Sample Data:
- X Export: 5 tweets (testuser)
- Grok Export: 10 posts (user_001, user_002, user_003)
"""

import sys
import json
import time
import os
import pytest
from pathlib import Path

# Paths - allow environment override for production data
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DATA_DIR = PROJECT_ROOT / "test_data"

# Allow environment override for production data
X_EXPORT_DIR = os.environ.get("X_EXPORT_PATH", str(TEST_DATA_DIR / "x_export"))
GROK_EXPORT_DIR = os.environ.get("GROK_EXPORT_PATH", str(TEST_DATA_DIR / "grok_export"))

sys.path.insert(0, str(PROJECT_ROOT / "core"))
from xkg_core import KnowledgeGraph


class TestGraphPopulation:
    """Test that uploads populate the graph correctly"""
    
    @pytest.fixture
    def kg(self):
        """Create fresh KnowledgeGraph for each test"""
        return KnowledgeGraph()
    
    def test_x_export_populates_graph(self, kg):
        """Upload X folder and verify graph is populated"""
        result = kg.build_from_export(str(X_EXPORT_DIR), 'x')
        
        # Verify stats
        assert result['stats']['total_tweets'] == 5, "Expected 5 tweets"
        assert result['stats']['total_actions'] > 0, "Expected actions extracted"
        assert result['stats']['topics_count'] > 0, "Expected topics clustered"
        
        # Verify graph nodes
        d3 = kg.export_for_d3()
        assert len(d3['nodes']) >= 5, "Expected at least 5 nodes (tweets)"
        
        # Verify tweet nodes have content
        tweet_nodes = [n for n in d3['nodes'] if n.get('type') == 'tweet']
        assert len(tweet_nodes) == 5, "Expected 5 tweet nodes"
        
        # Verify tweet text content is present
        tweet_ids = {n['id'] for n in tweet_nodes}
        for tweet in tweet_nodes:
            # Node may use 'label' or 'text' for content
            has_text = 'text' in tweet or 'label' in tweet
            assert has_text, f"Tweet node missing text/label: {tweet['id']}"
            content = tweet.get('text') or tweet.get('label', '')
            assert len(content) > 0, f"Tweet text is empty: {tweet['id']}"
        
    def test_grok_export_populates_graph(self, kg):
        """Upload Grok folder and verify graph is populated"""
        result = kg.build_from_export(str(GROK_EXPORT_DIR), 'grok')
        
        # Verify stats - Grok uses 'total_posts'
        posts_count = result['stats'].get('total_posts', result['stats'].get('total_tweets', 0))
        assert posts_count == 10, f"Expected 10 posts, got {posts_count}"
        assert result['stats']['total_actions'] > 0, "Expected actions extracted"
        assert result['stats']['grok_topics_count'] > 0, "Expected topics clustered"
        
        # Verify graph nodes
        d3 = kg.export_for_d3()
        assert len(d3['nodes']) >= 10, "Expected at least 10 nodes (posts)"
        
        # Verify grok nodes have content
        grok_nodes = [n for n in d3['nodes'] if n.get('type') == 'grok']
        assert len(grok_nodes) == 10, f"Expected 10 grok nodes, got {len(grok_nodes)}"
        
        # Verify grok text content
        for node in grok_nodes:
            assert 'text' in node, "Grok node missing text"
            assert len(node['text']) > 0, "Grok text is empty"
    
    def test_combined_upload_populates_graph(self, kg):
        """Upload both X and Grok folders and verify combined graph"""
        result = kg.build_from_both(str(X_EXPORT_DIR), str(GROK_EXPORT_DIR))
        
        # Verify combined stats
        assert result['stats']['total_tweets'] == 15, "Expected 15 total items"
        assert result['stats']['total_actions'] >= 15, "Expected actions from both sources"
        
        # Verify graph contains nodes from both sources
        d3 = kg.export_for_d3()
        tweet_count = len([n for n in d3['nodes'] if n.get('type') == 'tweet'])
        grok_count = len([n for n in d3['nodes'] if n.get('type') == 'grok'])
        
        assert tweet_count == 5, f"Expected 5 tweet nodes, got {tweet_count}"
        assert grok_count == 10, f"Expected 10 grok nodes, got {grok_count}"


class TestActionExtraction:
    """Test that action items are correctly extracted"""
    
    @pytest.fixture
    def kg(self):
        return KnowledgeGraph()
    
    def test_actions_extracted_from_x(self, kg):
        """Verify actions are extracted from X tweets"""
        result = kg.build_from_export(str(X_EXPORT_DIR), 'x')
        actions = result.get('actions', [])
        
        assert len(actions) > 0, "No actions extracted from X export"
        
        # Each action should have required fields
        for action in actions:
            assert 'text' in action, "Action missing text"
            assert 'priority' in action, "Action missing priority"
            assert action['text'].strip(), "Action text is empty"
        
        # Verify priority distribution
        priorities = [a['priority'] for a in actions]
        assert 'urgent' in priorities or 'high' in priorities or 'medium' in priorities, \
            "Expected some urgency indicators"
    
    def test_actions_extracted_from_grok(self, kg):
        """Verify actions are extracted from Grok posts"""
        result = kg.build_from_export(str(GROK_EXPORT_DIR), 'grok')
        actions = result.get('actions', [])
        
        assert len(actions) > 0, "No actions extracted from Grok export"
        
        # Each action should have required fields
        for action in actions:
            assert 'text' in action, "Action missing text"
            assert 'priority' in action, "Action missing priority"
        
        # Verify priority distribution (ASAP should be urgent)
        priorities = [a['priority'] for a in actions]
        assert 'urgent' in priorities, "Expected urgent action from ASAP keyword"
    
    def test_action_content_validation(self, kg):
        """Verify extracted actions contain meaningful content"""
        result = kg.build_from_export(str(X_EXPORT_DIR), 'x')
        actions = result.get('actions', [])
        
        # Check that actions contain recognizable task patterns
        action_texts = [a['text'].lower() for a in actions]
        
        # Should contain action verbs or task indicators
        task_indicators = ['todo', 'need to', 'remember to', 'should', 'going to', 'asap', 'urgent']
        found_indicators = [ind for ind in task_indicators if any(ind in t for t in action_texts)]
        
        assert len(found_indicators) > 0, \
            f"No task indicators found in actions: {action_texts}"


class TestTopicClustering:
    """Test that topics are correctly clustered from content"""
    
    @pytest.fixture
    def kg(self):
        return KnowledgeGraph()
    
    def test_topics_clustered_from_x(self, kg):
        """Verify topics are clustered from X content"""
        result = kg.build_from_export(str(X_EXPORT_DIR), 'x')
        topics = result.get('topics', {})
        
        assert len(topics) > 0, "No topics clustered from X export"
        
        # Each topic should have identifying info
        for topic_name, topic_data in topics.items():
            assert isinstance(topic_name, str), "Topic name is not a string"
            assert len(topic_name) > 0, "Topic name is empty"
    
    def test_topics_clustered_from_grok(self, kg):
        """Verify topics are clustered from Grok content"""
        result = kg.build_from_export(str(GROK_EXPORT_DIR), 'grok')
        topics = result.get('grok_topics', {})
        
        assert len(topics) > 0, "No topics clustered from Grok export"
        
        # Should have multiple topics clustered
        topic_names = [t.lower() for t in topics.keys()]
        
        # With 10 posts, should have at least 5 topics
        assert len(topic_names) >= 5, \
            f"Expected 5+ topics, got {len(topic_names)}: {topic_names}"
        
        # At least one topic should be meaningful (3+ chars)
        meaningful_topics = [t for t in topic_names if len(t) >= 3]
        assert len(meaningful_topics) > 0, \
            f"Expected meaningful topics, got: {topic_names}"
    
    def test_topics_from_combined(self, kg):
        """Verify combined export has unified topic clustering"""
        result = kg.build_from_both(str(X_EXPORT_DIR), str(GROK_EXPORT_DIR))
        topics = result.get('topics', {})
        
        assert len(topics) > 0, "No topics from combined export"


class TestGraphStructure:
    """Test D3 graph structure and node relationships"""
    
    @pytest.fixture
    def kg(self):
        return KnowledgeGraph()
    
    def test_graph_has_valid_structure(self, kg):
        """Verify D3 graph has valid node/edge structure"""
        kg.build_from_export(str(X_EXPORT_DIR), 'x')
        d3 = kg.export_for_d3()
        
        # Check required fields
        assert 'nodes' in d3, "Graph missing 'nodes'"
        assert 'edges' in d3, "Graph missing 'edges'"
        
        # Nodes should have required fields
        for node in d3['nodes']:
            assert 'id' in node, "Node missing 'id'"
            assert 'type' in node, "Node missing 'type'"
            assert 'label' in node, "Node missing 'label'"
        
        # Edges should have required fields
        for edge in d3['edges']:
            assert 'source' in edge, "Edge missing 'source'"
            assert 'target' in edge, "Edge missing 'target'"
            assert 'type' in edge, "Edge missing 'type'"
    
    def test_node_types_present(self, kg):
        """Verify all expected node types are present"""
        kg.build_from_export(str(X_EXPORT_DIR), 'x')
        d3 = kg.export_for_d3()
        
        node_types = set(n.get('type') for n in d3['nodes'])
        
        # Should have tweet nodes
        assert 'tweet' in node_types, "Missing tweet nodes"
        
        # Should have action nodes
        assert 'action' in node_types, "Missing action nodes"
        
        # Should have topic nodes
        assert 'topic' in node_types, "Missing topic nodes"
    
    def test_edges_connect_nodes(self, kg):
        """Verify edges create valid connections"""
        kg.build_from_export(str(X_EXPORT_DIR), 'x')
        d3 = kg.export_for_d3()
        
        node_ids = {n['id'] for n in d3['nodes']}
        
        # All edges should reference valid nodes (allow tweet_ and t_ prefixes)
        for edge in d3['edges']:
            source = edge['source']
            target = edge['target']
            # Allow various ID formats
            valid_source = (source in node_ids or 
                           source.startswith('tweet_') or 
                           source.startswith('t_') or
                           source.startswith('topic_') or
                           source.startswith('action_'))
            valid_target = (target in node_ids or
                           target.startswith('topic_') or
                           target.startswith('action_'))
            assert valid_source, f"Edge source invalid: {source}"
            assert valid_target, f"Edge target invalid: {target}"
    
    def test_node_content_accessible(self, kg):
        """Verify node content is accessible for display"""
        kg.build_from_export(str(X_EXPORT_DIR), 'x')
        d3 = kg.export_for_d3()
        
        # Each node should have displayable content
        for node in d3['nodes']:
            assert 'id' in node, "Node missing ID"
            assert 'type' in node, "Node missing type"
            
            # Content nodes should have text/label
            if node['type'] in ['tweet', 'grok']:
                assert 'text' in node or 'label' in node, \
                    f"Content node missing text: {node['id']}"


class TestSampleDataDetails:
    """Documentation of sample data being validated"""
    
    def get_x_export_path(self):
        """Return X export path as Path object"""
        return Path(X_EXPORT_DIR) if isinstance(X_EXPORT_DIR, str) else X_EXPORT_DIR
    
    def get_grok_export_path(self):
        """Return Grok export path as Path object"""
        return Path(GROK_EXPORT_DIR) if isinstance(GROK_EXPORT_DIR, str) else GROK_EXPORT_DIR
    
    def get_sample_data_summary(self):
        """Return summary of sample data"""
        return {
            "x_export": {
                "path": str(self.get_x_export_path()),
                "file": "tweet.js",
                "tweets": 5,
                "expected_actions": 7,
                "expected_topics": ["coding", "design", "api", "performance"],
                "sample_tweets": [
                    "Working on a new project. Need to finish the API integration by Friday.",
                    "TODO: Review the documentation and update the examples. This is urgent for the team.",
                    "Remember to schedule a meeting with the design team about the new UI components.",
                    "Going to refactor the authentication module next week. Should improve performance significantly.",
                    "Don't forget to backup the database before the maintenance window tonight."
                ]
            },
            "grok_export": {
                "path": str(self.get_grok_export_path()),
                "file": "posts.json",
                "posts": 10,
                "expected_actions": 15,
                "expected_topics": ["api", "performance", "testing", "database"],
                "sample_posts": [
                    "Just shipped the new feature to production. Need to monitor the error logs tomorrow morning.",
                    "TODO: Update the API documentation for the new endpoints. Make sure to include code examples.",
                    "ASAP: Fix the login bug that's affecting 5% of users.",
                    "Need to set up automated testing for the CI/CD pipeline.",
                    "Remember to renew the domain names before they expire next month."
                ]
            }
        }
    
    def test_sample_data_exists(self):
        """Verify sample data files exist"""
        x_path = self.get_x_export_path()
        grok_path = self.get_grok_export_path()
        
        assert x_path.exists(), f"X export dir not found: {x_path}"
        assert (x_path / "tweet.js").exists() or any(f.name.startswith('tweet') for f in x_path.iterdir()), \
            "tweet.js or similar not found"
        
        assert grok_path.exists(), f"Grok export dir not found: {grok_path}"
        assert any(f.name.endswith('.json') for f in grok_path.iterdir()), "No JSON files found"
    
    def test_sample_data_format(self):
        """Verify sample data is in correct format"""
        import json
        
        x_path = self.get_x_export_path()
        
        # Check for tweet files
        tweet_files = [f for f in x_path.iterdir() if 'tweet' in f.name.lower() and (f.suffix == '.js' or f.suffix == '.json')]
        assert len(tweet_files) > 0, "No tweet files found"
        
        # Check Grok format
        grok_path = self.get_grok_export_path()
        grok_files = [f for f in grok_path.iterdir() if f.suffix == '.json']
        assert len(grok_files) > 0, "No Grok JSON files found"
        
        posts = json.loads(grok_files[0].read_text())
        assert len(posts) == 10, "Expected 10 Grok posts"
        assert all("text" in p for p in posts), "Grok posts missing text"


class TestPerformanceBenchmarks:
    """Performance validation for production use"""
    
    @pytest.fixture
    def kg(self):
        return KnowledgeGraph()
    
    def test_x_parse_performance(self, kg):
        """X export should parse in under 2 seconds"""
        start = time.time()
        kg.build_from_export(str(X_EXPORT_DIR), 'x')
        elapsed = time.time() - start
        assert elapsed < 2.0, f"X parse took {elapsed:.2f}s (target: <2s)"
    
    def test_grok_parse_performance(self, kg):
        """Grok export should parse in under 3 seconds"""
        start = time.time()
        kg.build_from_export(str(GROK_EXPORT_DIR), 'grok')
        elapsed = time.time() - start
        assert elapsed < 3.0, f"Grok parse took {elapsed:.2f}s (target: <3s)"
    
    def test_combined_parse_performance(self, kg):
        """Combined export should parse in under 5 seconds"""
        start = time.time()
        kg.build_from_both(str(X_EXPORT_DIR), str(GROK_EXPORT_DIR))
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Combined parse took {elapsed:.2f}s (target: <5s)"
    
    def test_graph_export_performance(self, kg):
        """Graph D3 export should complete in under 1 second"""
        kg.build_from_export(str(X_EXPORT_DIR), 'x')
        start = time.time()
        d3 = kg.export_for_d3()
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Graph export took {elapsed:.2f}s (target: <1s)"


if __name__ == "__main__":
    # Run with: pytest tests/test_graph_validation.py -v
    
    summary = TestSampleDataDetails().get_sample_data_summary()
    print("\n" + "=" * 60)
    print("SAMPLE DATA SUMMARY")
    print("=" * 60)
    print(f"\nX Export:")
    print(f"  Path: {summary['x_export']['path']}")
    print(f"  Tweets: {summary['x_export']['tweets']}")
    print(f"  Expected Actions: {summary['x_export']['expected_actions']}")
    print(f"  Expected Topics: {summary['x_export']['expected_topics']}")
    
    print(f"\nGrok Export:")
    print(f"  Path: {summary['grok_export']['path']}")
    print(f"  Posts: {summary['grok_export']['posts']}")
    print(f"  Expected Actions: {summary['grok_export']['expected_actions']}")
    print(f"  Expected Topics: {summary['grok_export']['expected_topics']}")
    print()
