"""
Test Todoist Exporter
Validates the Todoist export functionality with mock API
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.todoist_exporter import (
    export_to_todoist,
    PRIORITY_MAP,
    TodoistExporter,
    TodoistExportResult
)


# Mock ActionItem for testing
class MockAction:
    def __init__(self, text, priority='medium', source_tweet_id='12345', topic='test', status='pending'):
        self.id = f"action_{hash(text) % 10000}"
        self.text = text
        self.priority = priority
        self.source_tweet_id = source_tweet_id
        self.topic = topic
        self.status = status
        self.created_at = '2026-02-12T00:00:00'


def test_priority_mapping():
    """Verify priority mapping is correct"""
    assert PRIORITY_MAP['urgent'] == 4, "urgent should map to p4"
    assert PRIORITY_MAP['high'] == 3, "high should map to p3"
    assert PRIORITY_MAP['medium'] == 2, "medium should map to p2"
    assert PRIORITY_MAP['low'] == 1, "low should map to p1"
    print("✅ Priority mapping test passed")


def test_mock_export():
    """Test export with mock API (no real token)"""
    actions = [
        MockAction("Buy groceries", priority='high'),
        MockAction("Finish report", priority='urgent'),
        MockAction("Call mom", priority='low'),
    ]
    
    # Export without token (uses mock mode)
    result = export_to_todoist(actions, api_token=None)
    
    assert result['success_count'] == 3, f"Expected 3 successes, got {result['success_count']}"
    assert result['failed_count'] == 0, f"Expected 0 failures, got {result['failed_count']}"
    assert len(result['task_ids']) == 3, "Should have 3 task IDs"
    
    print("✅ Mock export test passed")
    print(f"   Exported {result['success_count']} actions, got task_ids: {result['task_ids']}")


def test_priority_filter():
    """Test filtering by priority"""
    exporter = TodoistExporter(api_token=None, use_mock=True)
    
    actions = [
        MockAction("Urgent task", priority='urgent'),
        MockAction("High task", priority='high'),
        MockAction("Medium task", priority='medium'),
    ]
    
    # Export only urgent and high
    result = exporter.export_actions(actions, priority_filter=['urgent', 'high'])
    
    assert result['success_count'] == 2, f"Expected 2 successes, got {result['success_count']}"
    print("✅ Priority filter test passed")


def test_failure_simulation():
    """Test failure handling"""
    exporter = TodoistExporter(api_token=None, use_mock=True)
    
    # Test with content that triggers mock failure
    class FailAction:
        text = "fail_this_task"
        priority = 'medium'
        source_tweet_id = '12345'
        topic = 'test'
        status = 'pending'
        id = 'fail_1'
        created_at = '2026-02-12T00:00:00'
    
    result = exporter.export_action(FailAction())
    
    assert result.success == False, "Should fail for 'fail_*' content"
    assert result.error is not None, "Should have error message"
    
    print("✅ Failure simulation test passed")


if __name__ == '__main__':
    print("Running Todoist Exporter Tests...\n")
    
    test_priority_mapping()
    test_mock_export()
    test_priority_filter()
    test_failure_simulation()
    
    print("\n✅ All tests passed! Todoist export is working.")
