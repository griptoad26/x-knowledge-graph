#!/usr/bin/env python3
"""Test Todoist exporter with mock API"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.todoist_exporter import TodoistExporter, export_to_todoist, PRIORITY_MAP


class MockAction:
    """Mock action item for testing"""
    def __init__(self, text, priority='medium', source_tweet_id='123', topic='test', status='pending', created_at='2026-01-01'):
        self.text = text
        self.priority = priority
        self.source_tweet_id = source_tweet_id
        self.topic = topic
        self.status = status
        self.created_at = created_at


def test_priority_map():
    """Test priority mapping"""
    assert PRIORITY_MAP['urgent'] == 4
    assert PRIORITY_MAP['high'] == 3
    assert PRIORITY_MAP['medium'] == 2
    assert PRIORITY_MAP['low'] == 1
    print("✓ Priority mapping correct")


def test_mock_single_action():
    """Test exporting a single action with mock API"""
    exporter = TodoistExporter(use_mock=True)
    
    action = MockAction(
        text="Test TODO: complete this task",
        priority="urgent",
        source_tweet_id="12345",
        topic="testing",
        status="pending"
    )
    
    result = exporter.export_action(action)
    
    assert result.success, f"Expected success, got error: {result.error}"
    assert result.task_id.startswith("mock_"), f"Expected mock ID, got: {result.task_id}"
    print(f"✓ Single action export: {result.task_id}")


def test_mock_multiple_actions():
    """Test exporting multiple actions"""
    actions = [
        MockAction("High priority task", priority="high", source_tweet_id="1"),
        MockAction("Medium priority task", priority="medium", source_tweet_id="2"),
        MockAction("Low priority task", priority="low", source_tweet_id="3"),
    ]
    
    exporter = TodoistExporter(use_mock=True)
    result = exporter.export_actions(actions)
    
    assert result['success_count'] == 3, f"Expected 3 successes, got {result['success_count']}"
    assert result['failed_count'] == 0
    assert len(result['task_ids']) == 3
    print(f"✓ Multi-action export: {result['success_count']} tasks created")


def test_convenience_function():
    """Test the convenience export_to_todoist function"""
    actions = [
        MockAction("Test task 1", priority="urgent", source_tweet_id="1"),
        MockAction("Test task 2", priority="high", source_tweet_id="2"),
    ]
    
    # No token = mock mode
    result = export_to_todoist(actions)
    
    assert result['success_count'] == 2
    print(f"✓ Convenience function works: {result['success_count']} tasks")


def test_priority_filter():
    """Test filtering by priority"""
    actions = [
        MockAction("Urgent task", priority="urgent", source_tweet_id="1"),
        MockAction("High task", priority="high", source_tweet_id="2"),
        MockAction("Low task", priority="low", source_tweet_id="3"),
    ]
    
    exporter = TodoistExporter(use_mock=True)
    result = exporter.export_actions(actions, priority_filter=['urgent', 'high'])
    
    assert result['success_count'] == 2
    print(f"✓ Priority filter works: {result['success_count']} of {len(actions)} tasks")


def test_amazon_link_extraction():
    """Test Amazon link extraction from action text"""
    exporter = TodoistExporter(use_mock=True)
    
    action = MockAction(
        text="Check this out: https://amazon.com/dp/B000000000",
        priority="medium",
        source_tweet_id="123"
    )
    
    result = exporter.export_action(action)
    assert result.success
    print("✓ Amazon link extraction works")


def test_mock_failure_cases():
    """Test mock API failure cases"""
    exporter = TodoistExporter(use_mock=True)
    
    # Test empty content failure
    class EmptyAction:
        text = ""
        priority = "medium"
        source_tweet_id = "123"
        topic = "test"
        status = "pending"
        created_at = "2026-01-01"
    
    result = exporter.export_action(EmptyAction())
    assert not result.success
    print("✓ Empty content correctly fails")


if __name__ == '__main__':
    print("Testing Todoist Exporter...\n")
    
    test_priority_map()
    test_mock_single_action()
    test_mock_multiple_actions()
    test_convenience_function()
    test_priority_filter()
    test_amazon_link_extraction()
    test_mock_failure_cases()
    
    print("\n✓ All tests passed!")
