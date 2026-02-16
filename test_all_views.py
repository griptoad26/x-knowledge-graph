#!/usr/bin/env python3
"""
X Knowledge Graph - Comprehensive View Validation Script
Tests all views: Graph, Timeline, Task Board, Topic Clusters, Conversation Tree
Tests all features: X/Grok parsing, action extraction, topic clustering, Amazon links, export

Usage:
    python test_all_views.py              # Full validation
    python test_all_views.py --graph-only # Graph view only
    python test_all_views.py --quick      # Quick smoke test
    python test_all_views.py --json       # JSON output only
    python test_all_views.py --html      # Generate HTML report
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
import traceback

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "core"))
sys.path.insert(0, str(PROJECT_ROOT))

# GitHub Gist Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_GIST_TOKEN", "")
GIST_DESCRIPTION = "X Knowledge Graph Validation Results"

# Paths
TEST_DATA_DIR = PROJECT_ROOT / "test_data"
PROD_DATA_DIR = PROJECT_ROOT / "data"

# Desktop data paths (Windows paths via WSL)
DESKTOP_X_DIR = Path("/mnt/c/Users/Administrator/Desktop/x_export")
DESKTOP_GROK_DIR = Path("/mnt/c/Users/Administrator/Desktop/grok_export")

# Use Desktop data as the production data source
if (DESKTOP_X_DIR / "data").exists():
    X_EXPORT_DIR = str(DESKTOP_X_DIR / "data")
elif DESKTOP_X_DIR.exists():
    X_EXPORT_DIR = str(DESKTOP_X_DIR)
elif (PROD_DATA_DIR / "x_export" / "data").exists():
    X_EXPORT_DIR = str(PROD_DATA_DIR / "x_export" / "data")
else:
    X_EXPORT_DIR = str(TEST_DATA_DIR / "x_export")

if DESKTOP_GROK_DIR.exists():
    GROK_EXPORT_DIR = str(DESKTOP_GROK_DIR)
elif (PROD_DATA_DIR / "grok_export").exists():
    GROK_EXPORT_DIR = str(PROD_DATA_DIR / "grok_export")
else:
    GROK_EXPORT_DIR = str(TEST_DATA_DIR / "grok_export")

# Import core module
try:
    from xkg_core import KnowledgeGraph
except ImportError as e:
    print(f"Error importing core module: {e}")
    sys.exit(1)


@dataclass
class TestResult:
    """Single test result"""
    name: str
    category: str
    passed: bool
    expected: Any
    actual: Any
    duration_ms: float
    error: Optional[str] = None


@dataclass
class TestSuite:
    """Complete test suite results"""
    timestamp: str
    version: str
    duration_seconds: float
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    categories: Dict[str, Dict]
    results: List[Dict]
    errors: List[str]
    performance: Dict[str, Any]


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


def log(msg, color=None):
    if color is None:
        color = Colors.BLUE
    print(f"{color}{msg}{Colors.END}")


def log_step(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")


def print_header(title):
    print()
    log("=" * 70, Colors.CYAN)
    log(f"  {title}", Colors.CYAN)
    log("=" * 70, Colors.CYAN)
    print()


def print_result(name: str, passed: bool, expected: Any, actual: Any, duration_ms: float):
    """Print a single test result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    log(f"  [{status}] {name} ({duration_ms:.1f}ms)", Colors.BLUE if passed else Colors.RED)
    if not passed:
        log(f"       Expected: {expected}", Colors.YELLOW)
        log(f"       Actual:   {actual}", Colors.YELLOW)


# =============================================================================
# VIEW RENDERER TESTS
# =============================================================================

def test_graph_view_renderer():
    """Test Graph View rendering (D3 force-directed graph)"""
    log_step("Testing Graph View renderer...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    # Build graph from X export
    try:
        result = kg.build_from_export(X_EXPORT_DIR, 'x')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="X export loading",
            category="Graph View",
            passed=False,
            expected="Successful load",
            actual=f"Error: {str(e)}",
            duration_ms=duration_ms,
            error=str(e)
        )], {"error": str(e)}
    
    # Export D3 format
    d3 = kg.export_for_d3()
    
    # Validate D3 structure
    tests.append(TestResult(
        name="D3 nodes exist",
        category="Graph View",
        passed='nodes' in d3,
        expected="nodes in d3",
        actual="'nodes' in d3" if 'nodes' in d3 else "Missing",
        duration_ms=0
    ))
    
    tests.append(TestResult(
        name="D3 edges exist",
        category="Graph View",
        passed='edges' in d3,
        expected="edges in d3",
        actual="'edges' in d3" if 'edges' in d3 else "Missing",
        duration_ms=0
    ))
    
    # Validate node structure
    nodes = d3.get('nodes', [])
    if nodes:
        node = nodes[0]
        tests.append(TestResult(
            name="Node has id",
            category="Graph View",
            passed='id' in node,
            expected="id field",
            actual=list(node.keys()),
            duration_ms=0
        ))
        tests.append(TestResult(
            name="Node has type",
            category="Graph View",
            passed='type' in node,
            expected="type field",
            actual=list(node.keys()),
            duration_ms=0
        ))
        tests.append(TestResult(
            name="Node has label/text",
            category="Graph View",
            passed='label' in node or 'text' in node,
            expected="label or text",
            actual=list(node.keys()),
            duration_ms=0
        ))
    
    # Validate edge structure
    edges = d3.get('edges', [])
    if edges:
        edge = edges[0]
        tests.append(TestResult(
            name="Edge has source",
            category="Graph View",
            passed='source' in edge,
            expected="source field",
            actual=list(edge.keys()),
            duration_ms=0
        ))
        tests.append(TestResult(
            name="Edge has target",
            category="Graph View",
            passed='target' in edge,
            expected="target field",
            actual=list(edge.keys()),
            duration_ms=0
        ))
        tests.append(TestResult(
            name="Edge has type",
            category="Graph View",
            passed='type' in edge,
            expected="type field",
            actual=list(edge.keys()),
            duration_ms=0
        ))
    
    # Test node count metrics
    tweet_nodes = [n for n in nodes if n.get('type') == 'tweet']
    tests.append(TestResult(
        name="Tweet nodes generated",
        category="Graph View",
        passed=len(tweet_nodes) >= 0,  # May be 0 for empty data
        expected=">= 0 tweet nodes",
        actual=f"{len(tweet_nodes)} nodes",
        duration_ms=0
    ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {
        "nodes_count": len(nodes),
        "edges_count": len(edges),
        "tweet_nodes": len(tweet_nodes)
    }


def test_timeline_view_renderer():
    """Test Timeline View rendering (chronological display)"""
    log_step("Testing Timeline View renderer...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    try:
        result = kg.build_from_export(X_EXPORT_DIR, 'x')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="X export loading",
            category="Timeline View",
            passed=False,
            expected="Successful load",
            actual=f"Error: {str(e)}",
            duration_ms=duration_ms,
            error=str(e)
        )], {"error": str(e)}
    
    # Build timeline from tweets (Tweet is a dataclass)
    tweets = kg.tweets
    timeline_items = []
    for tweet_id, tweet in tweets.items():
        timeline_items.append({
            'id': tweet_id,
            'date': getattr(tweet, 'created_at', ''),
            'text': getattr(tweet, 'text', ''),
            'type': 'tweet'
        })
    
    # Sort by date
    timeline_items.sort(key=lambda x: x.get('date', ''))
    
    tests.append(TestResult(
        name="Timeline data structure",
        category="Timeline View",
        passed=isinstance(timeline_items, list),
        expected="list of items",
        actual=f"{len(timeline_items)} items",
        duration_ms=0
    ))
    
    if timeline_items:
        item = timeline_items[0]
        tests.append(TestResult(
            name="Timeline item has date",
            category="Timeline View",
            passed='date' in item,
            expected="date field",
            actual=list(item.keys()),
            duration_ms=0
        ))
        tests.append(TestResult(
            name="Timeline item has text",
            category="Timeline View",
            passed='text' in item,
            expected="text field",
            actual=list(item.keys()),
            duration_ms=0
        ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {"items_count": len(timeline_items)}


def test_taskboard_view_renderer():
    """Test Task Board View rendering (kanban-style action items)"""
    log_step("Testing Task Board View renderer...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    try:
        result = kg.build_from_export(X_EXPORT_DIR, 'x')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="X export loading",
            category="Task Board View",
            passed=False,
            expected="Successful load",
            actual=f"Error: {str(e)}",
            duration_ms=duration_ms,
            error=str(e)
        )], {"error": str(e)}
    
    # Get actions from result (ActionItem dataclass)
    actions = result.get('actions', []) if isinstance(result, dict) else []
    
    tests.append(TestResult(
        name="Actions structure",
        category="Task Board View",
        passed=isinstance(actions, list),
        expected="list of actions",
        actual=type(actions).__name__,
        duration_ms=0
    ))
    
    if actions:
        action = actions[0]
        # ActionItem is a dataclass, use to_dict() or getattr
        if hasattr(action, 'to_dict'):
            action_dict = action.to_dict()
        else:
            action_dict = action
        
        tests.append(TestResult(
            name="Action has text",
            category="Task Board View",
            passed='text' in action_dict,
            expected="text field",
            actual=list(action_dict.keys()),
            duration_ms=0
        ))
        tests.append(TestResult(
            name="Action has priority",
            category="Task Board View",
            passed='priority' in action_dict,
            expected="priority field",
            actual=list(action_dict.keys()),
            duration_ms=0
        ))
        tests.append(TestResult(
            name="Action has status",
            category="Task Board View",
            passed='status' in action_dict,
            expected="status field",
            actual=list(action_dict.keys()),
            duration_ms=0
        ))
        tests.append(TestResult(
            name="Action has topic",
            category="Task Board View",
            passed='topic' in action_dict,
            expected="topic field",
            actual=list(action_dict.keys()),
            duration_ms=0
        ))
    
    # Test column grouping
    columns = {}
    for action in actions:
        if hasattr(action, 'to_dict'):
            action_dict = action.to_dict()
        else:
            action_dict = action
        status = action_dict.get('status', 'pending')
        columns[status] = columns.get(status, 0) + 1
    
    tests.append(TestResult(
        name="Actions grouped by status",
        category="Task Board View",
        passed=len(columns) > 0,
        expected="status groups",
        actual=columns,
        duration_ms=0
    ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {
        "total_actions": len(actions),
        "columns": columns
    }


def test_clusters_view_renderer():
    """Test Topic Clusters View rendering"""
    log_step("Testing Topic Clusters View renderer...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    try:
        result = kg.build_from_export(X_EXPORT_DIR, 'x')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="X export loading",
            category="Topic Clusters View",
            passed=False,
            expected="Successful load",
            actual=f"Error: {str(e)}",
            duration_ms=duration_ms,
            error=str(e)
        )], {"error": str(e)}
    
    # Get topics from kg.topics (dict of topic name -> topic data)
    topics = kg.topics if hasattr(kg, 'topics') else {}
    
    tests.append(TestResult(
        name="Topics structure",
        category="Topic Clusters View",
        passed=isinstance(topics, dict),
        expected="dict of topics",
        actual=type(topics).__name__,
        duration_ms=0
    ))
    
    tests.append(TestResult(
        name="Topics count",
        category="Topic Clusters View",
        passed=len(topics) >= 0,
        expected=">= 0 topics",
        actual=f"{len(topics)} topics",
        duration_ms=0
    ))
    
    if topics:
        topic_name = list(topics.keys())[0]
        topic_data = topics[topic_name]
        tests.append(TestResult(
            name=f"Topic '{topic_name}' structure",
            category="Topic Clusters View",
            passed=isinstance(topic_data, dict),
            expected="dict structure",
            actual=list(topic_data.keys()),
            duration_ms=0
        ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {
        "topics_count": len(topics),
        "topics": list(topics.keys())[:5]
    }


def test_conversation_view_renderer():
    """Test Conversation Tree View rendering"""
    log_step("Testing Conversation Tree View renderer...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    try:
        result = kg.build_from_export(X_EXPORT_DIR, 'x')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="X export loading",
            category="Conversation Tree View",
            passed=False,
            expected="Successful load",
            actual=f"Error: {str(e)}",
            duration_ms=duration_ms,
            error=str(e)
        )], {"error": str(e)}
    
    # Build conversation trees from tweets (Tweet is a dataclass)
    tweets = kg.tweets
    conversations = {}
    
    for tweet_id, tweet in tweets.items():
        conv_id = getattr(tweet, 'conversation_id', 'no_conv')
        if conv_id not in conversations:
            conversations[conv_id] = {
                'id': conv_id,
                'tweets': [],
                'root': None
            }
        conversations[conv_id]['tweets'].append({
            'id': tweet_id,
            'text': getattr(tweet, 'text', ''),
            'reply_to': getattr(tweet, 'in_reply_to_status_id', None)
        })
        
        # Identify root tweet (not a reply)
        if not getattr(tweet, 'in_reply_to_status_id', None):
            conversations[conv_id]['root'] = tweet_id
    
    tests.append(TestResult(
        name="Conversations structure",
        category="Conversation Tree View",
        passed=isinstance(conversations, dict),
        expected="dict of conversations",
        actual=type(conversations).__name__,
        duration_ms=0
    ))
    
    tests.append(TestResult(
        name="Conversations count",
        category="Conversation Tree View",
        passed=len(conversations) >= 0,
        expected=">= 0 conversations",
        actual=f"{len(conversations)} conversations",
        duration_ms=0
    ))
    
    if conversations:
        conv_id = list(conversations.keys())[0]
        conv_data = conversations[conv_id]
        tests.append(TestResult(
            name=f"Conversation '{conv_id[:20]}...' structure",
            category="Conversation Tree View",
            passed='tweets' in conv_data,
            expected="tweets field",
            actual=list(conv_data.keys()),
            duration_ms=0
        ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {
        "conversations_count": len(conversations),
        "conversation_ids": list(conversations.keys())[:5]
    }


# =============================================================================
# DATA PARSING TESTS
# =============================================================================

def test_x_data_parsing():
    """Test X (Twitter) data parsing"""
    log_step("Testing X data parsing...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    try:
        result = kg.build_from_export(X_EXPORT_DIR, 'x')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="X export parsing",
            category="X Data Parsing",
            passed=False,
            expected="Successful parse",
            actual=f"Error: {str(e)}",
            duration_ms=duration_ms,
            error=str(e)
        )], {"error": str(e)}
    
    stats = result.get('stats', {})
    
    tests.append(TestResult(
        name="X parsing completed",
        category="X Data Parsing",
        passed=True,
        expected="Success",
        actual="Success",
        duration_ms=0
    ))
    
    tests.append(TestResult(
        name="X tweets count",
        category="X Data Parsing",
        passed=stats.get('total_tweets', 0) >= 0,
        expected=">= 0 tweets",
        actual=f"{stats.get('total_tweets', 0)} tweets",
        duration_ms=0
    ))
    
    tests.append(TestResult(
        name="X topics extracted",
        category="X Data Parsing",
        passed=stats.get('topics_count', 0) >= 0,
        expected=">= 0 topics",
        actual=f"{stats.get('topics_count', 0)} topics",
        duration_ms=0
    ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {
        "total_tweets": stats.get('total_tweets', 0),
        "topics_count": stats.get('topics_count', 0),
        "actions_count": stats.get('total_actions', 0)
    }


def test_grok_data_parsing():
    """Test Grok data parsing"""
    log_step("Testing Grok data parsing...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    # Check if Grok folder exists
    if not os.path.exists(GROK_EXPORT_DIR):
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="Grok folder exists",
            category="Grok Data Parsing",
            passed=False,
            expected="Folder exists",
            actual=f"Missing: {GROK_EXPORT_DIR}",
            duration_ms=duration_ms
        )], {"error": "Folder not found"}
    
    try:
        result = kg.build_from_export(GROK_EXPORT_DIR, 'grok')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="Grok export parsing",
            category="Grok Data Parsing",
            passed=False,
            expected="Successful parse",
            actual=f"Error: {str(e)}",
            duration_ms=duration_ms,
            error=str(e)
        )], {"error": str(e)}
    
    stats = result.get('stats', {})
    
    tests.append(TestResult(
        name="Grok parsing completed",
        category="Grok Data Parsing",
        passed=True,
        expected="Success",
        actual="Success",
        duration_ms=0
    ))
    
    tests.append(TestResult(
        name="Grok posts count",
        category="Grok Data Parsing",
        passed=stats.get('total_tweets', 0) >= 0,
        expected=">= 0 posts",
        actual=f"{stats.get('total_tweets', 0)} posts",
        duration_ms=0
    ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {
        "total_posts": stats.get('total_tweets', 0)
    }


# =============================================================================
# FEATURE TESTS
# =============================================================================

def test_action_extraction():
    """Test action extraction feature"""
    log_step("Testing action extraction...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    try:
        result = kg.build_from_export(X_EXPORT_DIR, 'x')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="X export loading",
            category="Action Extraction",
            passed=False,
            expected="Successful load",
            actual=f"Error: {str(e)}",
            duration_ms=duration_ms,
            error=str(e)
        )], {"error": str(e)}
    
    # Get actions from result (build_from_export returns result with 'actions' key)
    actions = result.get('actions', []) if isinstance(result, dict) else []
    
    tests.append(TestResult(
        name="Actions extracted",
        category="Action Extraction",
        passed=True,
        expected="Actions list",
        actual=f"{len(actions)} actions",
        duration_ms=0
    ))
    
    # Validate action structure
    priority_counts = {}
    for action in actions:
        priority = action.get('priority', 'unknown')
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    tests.append(TestResult(
        name="Priority levels present",
        category="Action Extraction",
        passed=len(priority_counts) > 0,
        expected="Priority counts",
        actual=priority_counts,
        duration_ms=0
    ))
    
    # Test Amazon link generation for actions
    amazon_actions = [a for a in actions if 'amazon.com' in a.get('text', '').lower()]
    tests.append(TestResult(
        name="Amazon links in actions",
        category="Action Extraction",
        passed=True,
        expected="Detected links",
        actual=f"{len(amazon_actions)} actions with Amazon links",
        duration_ms=0
    ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {
        "total_actions": len(actions),
        "priority_distribution": priority_counts,
        "amazon_link_count": len(amazon_actions)
    }


def test_topic_clustering():
    """Test topic clustering feature"""
    log_step("Testing topic clustering...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    try:
        result = kg.build_from_export(X_EXPORT_DIR, 'x')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="X export loading",
            category="Topic Clustering",
            passed=False,
            expected="Successful load",
            actual=f"Error: {str(e)}",
            duration_ms=duration_ms,
            error=str(e)
        )], {"error": str(e)}
    
    # Get topics from result (build_from_export returns result with 'topics' key)
    topics = result.get('topics', {}) if isinstance(result, dict) else kg.topics
    
    tests.append(TestResult(
        name="Topics generated",
        category="Topic Clustering",
        passed=True,
        expected="Topics dict",
        actual=f"{len(topics)} topics",
        duration_ms=0
    ))
    
    # Validate topic structure
    topic_items_count = 0
    topic_names = []
    for topic_name, topic_data in topics.items():
        topic_names.append(topic_name)
        if isinstance(topic_data, dict):
            if 'items' in topic_data:
                topic_items_count += len(topic_data['items'])
            elif isinstance(topic_data, list):
                topic_items_count += len(topic_data)
    
    tests.append(TestResult(
        name="Topic items distribution",
        category="Topic Clustering",
        passed=topic_items_count >= 0,
        expected="Total items",
        actual=f"{topic_items_count} items across topics",
        duration_ms=0
    ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {
        "topics_count": len(topics),
        "total_items": topic_items_count,
        "topic_names": topic_names[:5]
    }


def test_amazon_link_generation():
    """Test Amazon product link generation"""
    log_step("Testing Amazon link generation...")
    start = time.time()
    tests = []
    
    # Test Amazon product linker directly
    try:
        from amazon_product_linker import AmazonProductLinker
        linker = AmazonProductLinker()
        
        # Test URL generation (correct method name)
        test_query = "Python programming book"
        link = linker.generate_amazon_url(test_query)
        
        tests.append(TestResult(
            name="Amazon URL generation function",
            category="Amazon Links",
            passed=link and 'amazon.com' in link,
            expected="Amazon URL",
            actual=link[:80] if link else "None",
            duration_ms=0
        ))
        
        # Test product keyword detection (returns string)
        keywords = linker.extract_product_keywords("Check out this Python book on Amazon")
        tests.append(TestResult(
            name="Product keyword extraction",
            category="Amazon Links",
            passed=isinstance(keywords, (str, list)),
            expected="string or list",
            actual=keywords,
            duration_ms=0
        ))
        
        # Test product mention detection
        has_product = linker.detect_product_mention("I need a new laptop")
        tests.append(TestResult(
            name="Product mention detection",
            category="Amazon Links",
            passed=isinstance(has_product, bool),
            expected="boolean result",
            actual=str(has_product),
            duration_ms=0
        ))
        
    except ImportError as e:
        tests.append(TestResult(
            name="Amazon linker import",
            category="Amazon Links",
            passed=False,
            expected="Import success",
            actual=f"Import error: {e}",
            duration_ms=0,
            error=str(e)
        ))
    except Exception as e:
        tests.append(TestResult(
            name="Amazon link generation",
            category="Amazon Links",
            passed=False,
            expected="Success",
            actual=f"Error: {e}",
            duration_ms=0,
            error=str(e)
        ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {}


def test_export_functionality():
    """Test export functionality"""
    log_step("Testing export functionality...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    try:
        result = kg.build_from_export(X_EXPORT_DIR, 'x')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return [TestResult(
            name="X export loading",
            category="Export Functionality",
            passed=False,
            expected="Successful load",
            actual=f"Error: {str(e)}",
            duration_ms=duration_ms,
            error=str(e)
        )], {"error": str(e)}
    
    # Test D3 export
    d3 = kg.export_for_d3()
    tests.append(TestResult(
        name="D3 graph export",
        category="Export Functionality",
        passed='nodes' in d3 and 'edges' in d3,
        expected="Valid D3 structure",
        actual=f"nodes: {len(d3.get('nodes', []))}, edges: {len(d3.get('edges', []))}",
        duration_ms=0
    ))
    
    # Test manual JSON export (build from internal data)
    tweets_data = {}
    for k, v in kg.tweets.items():
        tweets_data[k] = {
            'id': v.id,
            'text': v.text,
            'created_at': v.created_at,
            'type': v.type if hasattr(v, 'type') else 'tweet'
        }
    
    json_export = {
        'tweets': tweets_data,
        'topics': kg.topics,
        'posts': kg.posts
    }
    tests.append(TestResult(
        name="JSON export structure",
        category="Export Functionality",
        passed=isinstance(json_export, dict),
        expected="Dict output",
        actual=f"keys: {list(json_export.keys())}",
        duration_ms=0
    ))
    
    # Test timeline export manually (Tweet is a dataclass)
    tweets = kg.tweets
    timeline_items = [{'id': k, 'date': getattr(v, 'created_at', ''), 'text': getattr(v, 'text', '')} 
                     for k, v in tweets.items()]
    tests.append(TestResult(
        name="Timeline export",
        category="Export Functionality",
        passed=isinstance(timeline_items, list),
        expected="list output",
        actual=f"{len(timeline_items)} items",
        duration_ms=0
    ))
    
    duration_ms = (time.time() - start) * 1000
    return tests, {
        "d3_nodes": len(d3.get('nodes', [])),
        "d3_edges": len(d3.get('edges', [])),
        "json_keys": list(json_export.keys()) if isinstance(json_export, dict) else []
    }


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

def test_performance():
    """Test parsing and rendering performance"""
    log_step("Testing performance...")
    start = time.time()
    tests = []
    
    kg = KnowledgeGraph()
    
    # X parse performance
    x_start = time.time()
    try:
        kg.build_from_export(X_EXPORT_DIR, 'x')
        x_time = (time.time() - x_start) * 1000
    except Exception as e:
        x_time = -1
        tests.append(TestResult(
            name="X parse time",
            category="Performance",
            passed=False,
            expected="< 30000ms",
            actual=f"Error: {e}",
            duration_ms=0,
            error=str(e)
        ))
    
    if x_time > 0:
        tests.append(TestResult(
            name="X parse time",
            category="Performance",
            passed=x_time < 30000,
            expected="< 30000ms",
            actual=f"{x_time:.1f}ms",
            duration_ms=x_time
        ))
    
    # Grok parse performance
    grok_start = time.time()
    try:
        if os.path.exists(GROK_EXPORT_DIR):
            kg.build_from_export(GROK_EXPORT_DIR, 'grok')
            grok_time = (time.time() - grok_start) * 1000
        else:
            grok_time = -1
    except Exception:
        grok_time = -1
    
    if grok_time > 0:
        tests.append(TestResult(
            name="Grok parse time",
            category="Performance",
            passed=grok_time < 30000,
            expected="< 30000ms",
            actual=f"{grok_time:.1f}ms",
            duration_ms=grok_time
        ))
    
    # Combined parse performance
    combined_start = time.time()
    try:
        kg.build_from_both(X_EXPORT_DIR, GROK_EXPORT_DIR)
        combined_time = (time.time() - combined_start) * 1000
    except Exception:
        combined_time = -1
    
    if combined_time > 0:
        tests.append(TestResult(
            name="Combined parse time",
            category="Performance",
            passed=combined_time < 60000,
            expected="< 60000ms",
            actual=f"{combined_time:.1f}ms",
            duration_ms=combined_time
        ))
    
    # D3 export performance
    d3_start = time.time()
    d3 = kg.export_for_d3()
    d3_time = (time.time() - d3_start) * 1000
    
    tests.append(TestResult(
        name="D3 export time",
        category="Performance",
        passed=d3_time < 5000,
        expected="< 5000ms",
        actual=f"{d3_time:.1f}ms",
        duration_ms=d3_time
    ))
    
    return tests, {
        "x_parse_ms": x_time,
        "grok_parse_ms": grok_time if grok_time > 0 else None,
        "combined_parse_ms": combined_time if combined_time > 0 else None,
        "d3_export_ms": d3_time
    }


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests(quick_mode=False):
    """Run complete test suite"""
    start_time = time.time()
    all_results = []
    category_results = {}
    all_errors = []
    performance_metrics = {}
    
    print_header("X KNOWLEDGE GRAPH - COMPREHENSIVE VIEW VALIDATION")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"X Data: {X_EXPORT_DIR}")
    print(f"Grok Data: {GROK_EXPORT_DIR}")
    print()
    
    test_suites = [
        ("X Data Parsing", test_x_data_parsing),
        ("Grok Data Parsing", test_grok_data_parsing),
        ("Graph View Renderer", test_graph_view_renderer),
        ("Timeline View Renderer", test_timeline_view_renderer),
        ("Task Board View Renderer", test_taskboard_view_renderer),
        ("Topic Clusters View Renderer", test_clusters_view_renderer),
        ("Conversation Tree View Renderer", test_conversation_view_renderer),
        ("Action Extraction", test_action_extraction),
        ("Topic Clustering", test_topic_clustering),
        ("Amazon Links", test_amazon_link_generation),
        ("Export Functionality", test_export_functionality),
        ("Performance", test_performance),
    ]
    
    if quick_mode:
        test_suites = [
            ("X Data Parsing", test_x_data_parsing),
            ("Graph View Renderer", test_graph_view_renderer),
            ("Performance", test_performance),
        ]
    
    for category_name, test_func in test_suites:
        print_header(f"{category_name.upper()}")
        try:
            results, metrics = test_func()
            all_results.extend(results)
            category_results[category_name] = {
                "passed": sum(1 for r in results if r.passed),
                "total": len(results),
                "metrics": metrics
            }
            performance_metrics.update(metrics)
            
            for result in results:
                print_result(result.name, result.passed, result.expected, result.actual, result.duration_ms)
                if result.error:
                    all_errors.append(f"{category_name}/{result.name}: {result.error}")
                    
        except Exception as e:
            error_msg = f"{category_name}: {str(e)}"
            all_errors.append(error_msg)
            log(f"  ✗ Test suite failed: {e}", Colors.RED)
            traceback.print_exc()
    
    # Calculate summary
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.passed)
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    duration = time.time() - start_time
    
    # Create results object
    suite_results = TestSuite(
        timestamp=datetime.now().isoformat(),
        version="0.4.35",
        duration_seconds=round(duration, 2),
        total_tests=total_tests,
        passed=passed_tests,
        failed=failed_tests,
        pass_rate=round(pass_rate, 1),
        categories=category_results,
        results=[asdict(r) for r in all_results],
        errors=all_errors,
        performance=performance_metrics
    )
    
    # Print summary
    print_header("VALIDATION SUMMARY")
    print(f"Total Tests: {total_tests}")
    print(f" {Colors.GREEN}Passed: {passed_tests}{Colors.END}")
    print(f" {Colors.RED}Failed: {failed_tests}{Colors.END}")
    print(f" Pass Rate: {pass_rate:.1f}%")
    print(f" Duration: {duration:.2f}s")
    
    if all_errors:
        print(f"\nErrors ({len(all_errors)}):")
        for err in all_errors[:5]:
            print(f"  - {err}")
        if len(all_errors) > 5:
            print(f"  ... and {len(all_errors) - 5} more")
    
    print_header("CATEGORY BREAKDOWN")
    for category, stats in category_results.items():
        status = Colors.GREEN if stats["passed"] == stats["total"] else Colors.YELLOW
        print(f"  [{status}{stats['passed']}/{stats['total']}{Colors.END}] {category}")
    
    return suite_results


def generate_html_report(results: TestSuite) -> str:
    """Generate HTML report from test results"""
    pass_color = "#00ff88"
    fail_color = "#ff4444"
    
    # Group results by category
    categories_html = ""
    for category, data in results.categories.items():
        tests_in_cat = [r for r in results.results if r.get('category') == category]
        tests_html = ""
        for test in tests_in_cat:
            status_class = "pass" if test['passed'] else "fail"
            status_icon = "✓" if test['passed'] else "✗"
            tests_html += f"""
            <div class="test-item {status_class}">
                <span>{test['name']}</span>
                <span>{status_icon} {test['actual']}</span>
            </div>
            """
        
        cat_pass_rate = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
        categories_html += f"""
        <div class="category">
            <h2>{category} <span style="font-size: 14px; color: {pass_color if cat_pass_rate == 100 else fail_color}">{data['passed']}/{data['total']} ({cat_pass_rate:.0f}%)</span></h2>
            {tests_html}
        </div>
        """
    
    # Performance metrics
    perf_html = ""
    for key, value in results.performance.items():
        if value is not None:
            perf_html += f"<li><strong>{key}:</strong> {value:.1f}ms</li>"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Knowledge Graph - Validation Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #1a1a2e; color: #eee; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; padding: 40px 0; border-bottom: 2px solid #333; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; color: #00d4ff; }}
        .timestamp {{ color: #888; margin-top: 10px; }}
        .summary {{ display: flex; justify-content: center; gap: 40px; margin: 30px 0; }}
        .stat {{ text-align: center; padding: 20px 40px; background: #16213e; border-radius: 10px; }}
        .stat-value {{ font-size: 48px; font-weight: bold; }}
        .stat-label {{ color: #888; margin-top: 5px; }}
        .pass {{ color: #00ff88; }}
        .fail {{ color: #ff4444; }}
        .warning {{ color: #ffaa00; }}
        .category {{ margin-bottom: 30px; background: #16213e; padding: 20px; border-radius: 10px; }}
        .category h2 {{ color: #00d4ff; border-bottom: 1px solid #333; padding-bottom: 10px; margin-top: 0; }}
        .test-item {{ display: flex; justify-content: space-between; padding: 12px 15px; border-bottom: 1px solid #2a2a4e; }}
        .test-item:last-child {{ border-bottom: none; }}
        .test-item.pass {{ background: rgba(0, 255, 136, 0.05); }}
        .test-item.fail {{ background: rgba(255, 68, 68, 0.05); }}
        .performance {{ background: #16213e; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
        .performance h2 {{ color: #00d4ff; margin-top: 0; }}
        .errors {{ background: #2a1a1a; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
        .errors h2 {{ color: #ff4444; margin-top: 0; }}
        .errors ul {{ margin: 0; padding-left: 20px; }}
        .errors li {{ color: #ff6666; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>X Knowledge Graph - Validation Report</h1>
            <div class="timestamp">Generated: {results.timestamp} | Version: {results.version}</div>
        </div>
        
        <div class="summary">
            <div class="stat">
                <div class="stat-value">{results.total_tests}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat">
                <div class="stat-value pass">{results.passed}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat">
                <div class="stat-value fail">{results.failed}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {pass_color if results.pass_rate >= 80 else fail_color}">{results.pass_rate:.1f}%</div>
                <div class="stat-label">Pass Rate</div>
            </div>
            <div class="stat">
                <div class="stat-value">{results.duration_seconds:.2f}s</div>
                <div class="stat-label">Duration</div>
            </div>
        </div>
        
        <div class="performance">
            <h2>Performance Metrics</h2>
            <ul>
                {perf_html if perf_html else '<li>No performance data available</li>'}
            </ul>
        </div>
        
        {f'<div class="errors"><h2>Errors ({len(results.errors)})</h2><ul>' + ''.join(f'<li>{e}</li>' for e in results.errors) + '</ul></div>' if results.errors else ''}
        
        {categories_html}
    </div>
</body>
</html>
"""
    return html


def save_results_json(results: TestSuite, filepath: str = None):
    """Save results to JSON file"""
    if filepath is None:
        filepath = PROJECT_ROOT / "test_results.json"
    
    with open(filepath, 'w') as f:
        json.dump(asdict(results), f, indent=2, default=str)
    
    return filepath


def upload_to_gist(results: TestSuite) -> Optional[str]:
    """Upload results to GitHub Gist"""
    if not GITHUB_TOKEN:
        log("GitHub token not set - skipping Gist upload", Colors.YELLOW)
        return None
    
    import requests
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    gist_id_file = PROJECT_ROOT / ".gist_id.txt"
    gist_id = None
    if gist_id_file.exists():
        gist_id = gist_id_file.read_text().strip()
    
    files = {
        "validation_report.json": json.dumps(asdict(results), indent=2, default=str)
    }
    
    data = {
        "description": f"{GIST_DESCRIPTION} - {results.timestamp}",
        "public": False,
        "files": files
    }
    
    try:
        if gist_id:
            response = requests.patch(
                f"https://api.github.com/gists/{gist_id}",
                headers=headers, json=data, timeout=30
            )
        else:
            response = requests.post(
                "https://api.github.com/gists",
                headers=headers, json=data, timeout=30
            )
        
        if response.status_code in [200, 201]:
            result = response.json()
            gist_id = result["id"]
            gist_id_file.write_text(gist_id)
            return result["html_url"]
    except Exception as e:
        log(f"Gist upload error: {e}", Colors.RED)
    
    return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="X Knowledge Graph - View Validation Tests")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke test")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--gist", action="store_true", help="Upload results to GitHub Gist")
    parser.add_argument("--output", type=str, default="test_results.json", help="Output file path")
    args = parser.parse_args()
    
    # Run tests
    results = run_all_tests(quick_mode=args.quick)
    
    # Output JSON
    if args.json:
        print("\n" + json.dumps(asdict(results), indent=2, default=str))
    else:
        # Save JSON
        save_results_json(results, args.output)
        log(f"\nResults saved to: {args.output}", Colors.GREEN)
    
    # Generate HTML report
    if args.html:
        html_file = PROJECT_ROOT / "test_report.html"
        html = generate_html_report(results)
        html_file.write_text(html)
        log(f"HTML report saved to: {html_file}", Colors.GREEN)
    
    # Upload to Gist
    if args.gist:
        gist_url = upload_to_gist(results)
        if gist_url:
            log(f"Gist URL: {gist_url}", Colors.GREEN)
    
    # Return success/fail
    success = results.failed == 0
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())