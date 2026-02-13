#!/usr/bin/env python3
"""Test Todoist exporter with mock API"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.todoist_exporter import export_to_todoist, TodoistExporter, PRIORITY_MAP

# Mock ActionItem class
class MockAction:
    def __init__(self, text, priority='medium', source_tweet_id='123', topic='test', status='pending'):
        self.text = text
        self.priority = priority
        self.source_tweet_id = source_tweet_id
        self.topic = topic
        self.status = status
        self.created_at = '2026-02-01T00:00:00'

def test_priority_mapping():
    """Test priority mapping"""
    print("Testing priority mapping...")
    assert PRIORITY_MAP['urgent'] == 4, "urgent should map to p4"
    assert PRIORITY_MAP['high'] == 3, "high should map to p3"
    assert PRIORITY_MAP['medium'] == 2, "medium should map to p2"
    assert PRIORITY_MAP['low'] == 1, "low should map to p1"
    print("✅ Priority mapping correct")

def test_mock_export():
    """Test export with mock API"""
    print("\nTesting mock API export...")
    
    actions = [
        MockAction("TODO: Follow up with client", "high", "tweet_001", "business", "pending"),
        MockAction("ASAP: Review the proposal", "urgent", "tweet_002", "sales", "pending"),
        MockAction("need to call mom", "medium", "tweet_003", "personal", "pending"),
    ]
    
    # Export without token (uses mock)
    result = export_to_todoist(actions, api_token=None)
    
    print(f"Export result: {result}")
    
    assert result['success_count'] == 3, f"Expected 3 successes, got {result['success_count']}"
    assert result['failed_count'] == 0, f"Expected 0 failures, got {result['failed_count']}"
    assert len(result['task_ids']) == 3, "Should have 3 task IDs"
    assert len(result['errors']) == 0, "Should have no errors"
    
    print("✅ Mock export successful")
    
    # Test individual exporter
    print("\nTesting individual exporter...")
    exporter = TodoistExporter(api_token=None, use_mock=True)
    single_result = exporter.export_action(actions[0])
    
    assert single_result.success, "Single export should succeed"
    assert single_result.task_id is not None, "Should have task_id"
    print(f"✅ Single action exported: {single_result.task_id}")

def test_failure_cases():
    """Test mock failure cases"""
    print("\nTesting failure cases...")
    
    class FailAction:
        text = ""
        priority = "medium"
        source_tweet_id = "fail_test"
        topic = "test"
        status = "pending"
        created_at = "2026-02-01T00:00:00"
    
    exporter = TodoistExporter(api_token=None, use_mock=True)
    result = exporter.export_action(FailAction())
    
    assert not result.success, "Should fail with empty content"
    assert result.error is not None, "Should have error message"
    print(f"✅ Failure case handled: {result.error}")

def test_export_to_todoist_function():
    """Test the main export_to_todoist convenience function"""
    print("\nTesting export_to_todoist() convenience function...")
    
    actions = [
        MockAction("TODO: Test task", "low", "tweet_001", "test", "pending"),
    ]
    
    # Use None to trigger mock mode
    result = export_to_todoist(actions, api_token=None)
    
    assert result['success_count'] == 1, "Should succeed with mock"
    print("✅ export_to_todoist() works correctly")

if __name__ == '__main__':
    print("=" * 50)
    print("Todoist Exporter Test Suite")
    print("=" * 50)
    
    test_priority_mapping()
    test_mock_export()
    test_failure_cases()
    test_export_to_todoist_function()
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed!")
    print("=" * 50)
