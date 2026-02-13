#!/usr/bin/env python3
"""
Test Todoist CLI integration
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.todoist_exporter import TodoistExporter, PRIORITY_MAP
from dataclasses import dataclass


@dataclass
class MockAction:
    text: str
    priority: str
    source_tweet_id: str = "test_123"
    topic: str = "test"
    status: str = "pending"


def test_cli_export_todoist():
    """Simulate CLI export-todoist command"""
    # Mock args
    token = "mock_token"
    graph = "combined"
    priority_filter = None
    use_mock = True
    
    # Create mock actions
    actions = [
        MockAction(text="Test action 1", priority="urgent", source_tweet_id="1"),
        MockAction(text="Test action 2", priority="high", source_tweet_id="2"),
        MockAction(text="Test action 3", priority="medium", source_tweet_id="3"),
    ]
    
    # Export
    exporter = TodoistExporter(use_mock=use_mock)
    result = exporter.export_actions(actions, priority_filter=priority_filter)
    
    # Verify
    assert result['success_count'] == 3, f"Expected 3, got {result['success_count']}"
    assert len(result['task_ids']) == 3
    assert result['failed_count'] == 0
    
    print("✅ CLI export-todoist simulation passed")
    print(f"   Token: {token}")
    print(f"   Graph: {graph}")
    print(f"   Exported: {result['success_count']} actions")
    print(f"   Task IDs: {result['task_ids']}")


def test_cli_with_priority_filter():
    """Simulate CLI export with priority filter"""
    actions = [
        MockAction(text="Urgent only", priority="urgent", source_tweet_id="1"),
        MockAction(text="High only", priority="high", source_tweet_id="2"),
        MockAction(text="Medium only", priority="medium", source_tweet_id="3"),
    ]
    
    # Simulate: xkg export-todoist <token> --priority urgent high
    exporter = TodoistExporter(use_mock=True)
    result = exporter.export_actions(actions, priority_filter=['urgent', 'high'])
    
    assert result['success_count'] == 2
    assert result['total'] == 2
    
    print("✅ CLI priority filter passed")
    print(f"   Filtered: urgent, high")
    print(f"   Exported: {result['success_count']} actions")


if __name__ == "__main__":
    print("Running Todoist CLI Integration Tests...\n")
    test_cli_export_todoist()
    test_cli_with_priority_filter()
    print("\n✅ All CLI integration tests passed!")
