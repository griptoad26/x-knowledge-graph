#!/usr/bin/env python3
"""Test Todoist exporter with mock API"""

import sys
import os

# Add the project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.todoist_exporter import (
    TodoistExporter, 
    export_to_todoist, 
    PRIORITY_MAP,
    TodoistExportResult
)

# Mock ActionItem class for testing
class MockAction:
    def __init__(self, text, priority='medium', topic='test', status='pending', source_tweet_id='123'):
        self.id = f'action_{hash(text) % 10000}'
        self.text = text
        self.priority = priority
        self.topic = topic
        self.status = status
        self.source_tweet_id = source_tweet_id
        self.created_at = '2026-02-12T00:00:00'


def test_priority_map():
    """Test priority mapping"""
    expected = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}
    assert PRIORITY_MAP == expected, f"Priority map mismatch: {PRIORITY_MAP}"
    print("✓ Priority mapping correct")


def test_mock_exporter_single_action():
    """Test exporting a single action with mock API"""
    exporter = TodoistExporter(use_mock=True)
    
    action = MockAction("Buy Amazon product", priority='high')
    result = exporter.export_action(action)
    
    assert result.success, f"Export failed: {result.error}"
    assert result.task_id is not None, "No task_id returned"
    assert result.task_id.startswith('mock_'), f"Invalid task_id format: {result.task_id}"
    print(f"✓ Single action exported: {result.task_id}")


def test_mock_exporter_multiple_actions():
    """Test exporting multiple actions"""
    actions = [
        MockAction("Urgent task", priority='urgent'),
        MockAction("High priority", priority='high'),
        MockAction("Medium task", priority='medium'),
        MockAction("Low priority", priority='low'),
    ]
    
    result = export_to_todoist(actions, api_token=None)  # No token = mock mode
    
    assert result['success_count'] == 4, f"Expected 4 successes, got {result['success_count']}"
    assert result['failed_count'] == 0, f"Expected 0 failures, got {result['failed_count']}"
    assert len(result['task_ids']) == 4, f"Expected 4 task_ids, got {len(result['task_ids'])}"
    print(f"✓ Multiple actions exported: {result['success_count']} successes")


def test_mock_failure_cases():
    """Test mock failure scenarios"""
    exporter = TodoistExporter(use_mock=True)
    
    # Empty content should fail
    result = exporter.export_action(MockAction(""))
    assert not result.success, "Empty content should fail"
    assert "invalid task content" in result.error.lower(), f"Wrong error: {result.error}"
    print("✓ Empty content correctly fails")
    
    # network_error should fail
    result = exporter.export_action(MockAction("network_error"))
    assert not result.success, "network_error should fail"
    assert "network error" in result.error.lower(), f"Wrong error: {result.error}"
    print("✓ Network error correctly fails")


def test_amazon_link_extraction():
    """Test Amazon link extraction from action text"""
    exporter = TodoistExporter(use_mock=True)
    
    # Test various Amazon link formats
    test_cases = [
        ("Check this https://amazon.com/dp/B000 test", "https://amazon.com/dp/B000"),
        ("Buy at https://amzn.to/abc123", "https://amzn.to/abc123"),
        ("amazon.com/dp/XYZ", "amazon.com/dp/XYZ"),
    ]
    
    for text, expected in test_cases:
        extracted = exporter._extract_amazon_link(text)
        assert extracted == expected, f"For '{text[:30]}...': expected {expected}, got {extracted}"
    
    print("✓ Amazon link extraction works")


def test_priority_values():
    """Verify priority values are Todoist-compatible (1-4)"""
    for priority, value in PRIORITY_MAP.items():
        assert 1 <= value <= 4, f"Priority {priority} has invalid value {value} (must be 1-4)"
    print("✓ All priorities in valid range (1-4)")


if __name__ == '__main__':
    print("Running Todoist exporter tests...\n")
    
    test_priority_map()
    test_priority_values()
    test_amazon_link_extraction()
    test_mock_exporter_single_action()
    test_mock_exporter_multiple_actions()
    test_mock_failure_cases()
    
    print("\n✓ All tests passed!")
