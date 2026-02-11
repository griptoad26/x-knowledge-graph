"""
Tests for Todoist Exporter
Tests the Todoist API integration with mocked responses
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict

# Import only the todoist_exporter which is self-contained
from core.todoist_exporter import TodoistExporter, PRIORITY_MAP


# Minimal ActionItem for testing (matches xkg_core.py)
@dataclass
class ActionItem:
    id: str
    text: str
    source_tweet_id: str
    topic: str
    priority: str  # urgent, high, medium, low
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


def test_priority_map():
    """Test priority mapping from XKG to Todoist"""
    assert PRIORITY_MAP['urgent'] == 4, "urgent should map to 4 (p1)"
    assert PRIORITY_MAP['high'] == 3, "high should map to 3 (p2)"
    assert PRIORITY_MAP['medium'] == 2, "medium should map to 2 (p3)"
    assert PRIORITY_MAP['low'] == 1, "low should map to 1 (p4)"
    print("✅ Priority mapping tests passed")


def test_mock_exporter_basic():
    """Test basic mock export functionality"""
    exporter = TodoistExporter(use_mock=True)
    
    # Create a test action
    action = ActionItem(
        id='test_1',
        text='Buy groceries',
        source_tweet_id='123456',
        topic='personal',
        priority='high',
        status='pending'
    )
    
    result = exporter.export_action(action)
    assert result.success, f"Expected success, got error: {result.error}"
    assert result.task_id.startswith('mock_'), f"Expected mock ID, got: {result.task_id}"
    print(f"✅ Basic mock export passed (task_id: {result.task_id})")


def test_mock_export_with_amazon_link():
    """Test export with Amazon link in description"""
    exporter = TodoistExporter(use_mock=True)
    
    action = ActionItem(
        id='test_2',
        text='Check out this product https://amzn.to/abc123',
        source_tweet_id='789',
        topic='shopping',
        priority='urgent',
        status='pending'
    )
    
    result = exporter.export_action(action)
    assert result.success, f"Expected success, got error: {result.error}"
    print("✅ Amazon link export test passed")


def test_mock_export_multiple():
    """Test exporting multiple actions"""
    exporter = TodoistExporter(use_mock=True)
    
    actions = [
        ActionItem(id=f'action_{i}', text=f'Task {i}', source_tweet_id=str(i),
                   topic='test', priority=['urgent', 'high', 'medium'][i % 3],
                   status='pending')
        for i in range(5)
    ]
    
    result = exporter.export_actions(actions)
    assert result['success_count'] == 5, f"Expected 5 successes, got {result['success_count']}"
    assert result['failed_count'] == 0, f"Expected 0 failures, got {result['failed_count']}"
    assert len(result['task_ids']) == 5
    print(f"✅ Multi-export test passed ({result['success_count']} tasks)")


def test_priority_filter():
    """Test exporting with priority filter"""
    exporter = TodoistExporter(use_mock=True)
    
    actions = [
        ActionItem(id='a1', text='Urgent task', source_tweet_id='1',
                   topic='test', priority='urgent', status='pending'),
        ActionItem(id='a2', text='High task', source_tweet_id='2',
                   topic='test', priority='high', status='pending'),
        ActionItem(id='a3', text='Low task', source_tweet_id='3',
                   topic='test', priority='low', status='pending'),
    ]
    
    # Only export urgent and high
    result = exporter.export_actions(actions, priority_filter=['urgent', 'high'])
    assert result['success_count'] == 2, f"Expected 2, got {result['success_count']}"
    assert result['total'] == 2
    print("✅ Priority filter test passed")


def test_date_filter():
    """Test exporting with date filter"""
    exporter = TodoistExporter(use_mock=True)
    
    actions = [
        ActionItem(id='a1', text='Old task', source_tweet_id='1',
                   topic='test', priority='medium', status='pending',
                   created_at='2024-01-01T10:00:00'),
        ActionItem(id='a2', text='New task', source_tweet_id='2',
                   topic='test', priority='medium', status='pending',
                   created_at='2025-01-01T10:00:00'),
    ]
    
    # Only export tasks from 2025
    result = exporter.export_actions(
        actions,
        date_from='2025-01-01T00:00:00',
        date_to='2025-12-31T23:59:59'
    )
    assert result['success_count'] == 1, f"Expected 1, got {result['success_count']}"
    print("✅ Date filter test passed")


def test_mock_failure():
    """Test mock failure handling"""
    exporter = TodoistExporter(use_mock=True)
    
    # Create action that will fail (starts with 'fail')
    action = ActionItem(
        id='fail_1',
        text='fail_this_task',
        source_tweet_id='123',
        topic='test',
        priority='low',
        status='pending'
    )
    
    result = exporter.export_action(action)
    assert not result.success, "Expected failure for 'fail' task"
    assert 'invalid task content' in result.error.lower()
    print("✅ Mock failure test passed")


def test_mock_network_error():
    """Test mock network error handling"""
    exporter = TodoistExporter(use_mock=True)
    
    action = ActionItem(
        id='net_1',
        text='network_error',
        source_tweet_id='123',
        topic='test',
        priority='low',
        status='pending'
    )
    
    result = exporter.export_action(action)
    assert not result.success, "Expected failure for network_error task"
    assert 'network error' in result.error.lower()
    print("✅ Mock network error test passed")


def test_empty_export():
    """Test exporting with no actions"""
    exporter = TodoistExporter(use_mock=True)
    result = exporter.export_actions([])
    assert result['success_count'] == 0
    assert result['failed_count'] == 0
    print("✅ Empty export test passed")


def test_case_insensitive_priority():
    """Test that priority filter is case insensitive"""
    exporter = TodoistExporter(use_mock=True)
    
    actions = [
        ActionItem(id='a1', text='URGENT task', source_tweet_id='1',
                   topic='test', priority='urgent', status='pending'),
        ActionItem(id='a2', text='Urgent task', source_tweet_id='2',
                   topic='test', priority='URGENT', status='pending'),
        ActionItem(id='a3', text='High task', source_tweet_id='3',
                   topic='test', priority='high', status='pending'),
    ]
    
    result = exporter.export_actions(actions, priority_filter=['urgent'])
    assert result['success_count'] == 2, f"Expected 2, got {result['success_count']}"
    print("✅ Case insensitive priority test passed")


if __name__ == '__main__':
    print("Running Todoist Exporter tests...\n")
    
    test_priority_map()
    test_mock_exporter_basic()
    test_mock_export_with_amazon_link()
    test_mock_export_multiple()
    test_priority_filter()
    test_date_filter()
    test_mock_failure()
    test_mock_network_error()
    test_empty_export()
    test_case_insensitive_priority()
    
    print("\n🎉 All Todoist Exporter tests passed!")
