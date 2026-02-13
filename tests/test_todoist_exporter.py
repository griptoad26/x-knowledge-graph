"""
Test Todoist Exporter with Mock API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.todoist_exporter import TodoistExporter, PRIORITY_MAP, TodoistExportResult, export_to_todoist
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MockAction:
    """Mock ActionItem for testing"""
    text: str
    priority: str
    source_tweet_id: str = "test_123"
    topic: str = "test"
    status: str = "pending"
    created_at: str = "2026-02-12T00:00:00"


def test_priority_mapping():
    """Test priority mapping"""
    assert PRIORITY_MAP['urgent'] == 4
    assert PRIORITY_MAP['high'] == 3
    assert PRIORITY_MAP['medium'] == 2
    assert PRIORITY_MAP['low'] == 1
    print("✓ Priority mapping test passed")


def test_mock_single_action():
    """Test exporting a single action with mock API"""
    exporter = TodoistExporter(use_mock=True)
    
    action = MockAction(
        text="Test action: Buy coffee",
        priority="high",
        source_tweet_id="123"
    )
    
    result = exporter.export_action(action)
    
    assert result.success, f"Expected success, got error: {result.error}"
    assert result.task_id is not None
    assert result.task_id.startswith("mock_")
    print("✓ Single action export test passed")


def test_mock_multiple_actions():
    """Test exporting multiple actions"""
    exporter = TodoistExporter(use_mock=True)
    
    actions = [
        MockAction(text="Action 1", priority="urgent", source_tweet_id="1"),
        MockAction(text="Action 2", priority="high", source_tweet_id="2"),
        MockAction(text="Action 3", priority="medium", source_tweet_id="3"),
        MockAction(text="Action 4", priority="low", source_tweet_id="4"),
    ]
    
    result = exporter.export_actions(actions)
    
    assert result['success_count'] == 4
    assert result['failed_count'] == 0
    assert len(result['task_ids']) == 4
    print("✓ Multiple actions export test passed")


def test_priority_filter():
    """Test filtering by priority"""
    exporter = TodoistExporter(use_mock=True)
    
    actions = [
        MockAction(text="Urgent task", priority="urgent", source_tweet_id="1"),
        MockAction(text="Low task", priority="low", source_tweet_id="2"),
        MockAction(text="High task", priority="high", source_tweet_id="3"),
    ]
    
    # Filter only urgent and high
    result = exporter.export_actions(actions, priority_filter=['urgent', 'high'])
    
    assert result['success_count'] == 2
    assert result['total'] == 2
    print("✓ Priority filter test passed")


def test_mock_failure():
    """Test mock failure scenarios"""
    exporter = TodoistExporter(use_mock=True)
    
    # Empty content should fail
    action = MockAction(text="", priority="medium", source_tweet_id="1")
    result = exporter.export_action(action)
    
    assert not result.success
    assert "invalid task content" in result.error.lower()
    print("✓ Mock failure test passed")


def test_mock_network_error():
    """Test mock network error simulation"""
    exporter = TodoistExporter(use_mock=True)
    
    # Simulate network error
    action = MockAction(text="network_error", priority="medium", source_tweet_id="1")
    result = exporter.export_action(action)
    
    assert not result.success
    assert "network error" in result.error.lower()
    print("✓ Mock network error test passed")


def test_convenience_function():
    """Test the convenience export_to_todoist function"""
    actions = [
        MockAction(text="Quick task", priority="low", source_tweet_id="1"),
    ]
    
    # No token = mock mode
    result = export_to_todoist(actions)
    
    assert result['success_count'] == 1
    assert len(result['task_ids']) == 1
    print("✓ Convenience function test passed")


def test_task_payload():
    """Test that task payload is built correctly"""
    exporter = TodoistExporter(use_mock=True)
    
    action = MockAction(
        text="Buy the new iPhone 15 Pro",
        priority="high",
        source_tweet_id="456",
        topic="shopping"
    )
    
    payload = exporter._build_task_payload(action)
    
    assert payload['content'] == "Buy the new iPhone 15 Pro"
    assert payload['priority'] == PRIORITY_MAP['high']
    assert 'X Knowledge Graph' in payload['description']
    assert 'HIGH' in payload['description']
    assert '456' in payload['description']
    print("✓ Task payload test passed")


def test_mock_responses_tracking():
    """Test mock responses are tracked"""
    exporter = TodoistExporter(use_mock=True)
    
    actions = [
        MockAction(text="Task 1", priority="low", source_tweet_id="1"),
        MockAction(text="Task 2", priority="low", source_tweet_id="2"),
    ]
    
    exporter.export_actions(actions)
    
    responses = exporter.get_mock_responses()
    assert len(responses) == 2
    
    exporter.clear_mock_responses()
    assert len(exporter.get_mock_responses()) == 0
    print("✓ Mock responses tracking test passed")


if __name__ == "__main__":
    print("Running Todoist Exporter Tests...\n")
    
    test_priority_mapping()
    test_mock_single_action()
    test_mock_multiple_actions()
    test_priority_filter()
    test_mock_failure()
    test_mock_network_error()
    test_convenience_function()
    test_task_payload()
    test_mock_responses_tracking()
    
    print("\n✅ All tests passed!")
