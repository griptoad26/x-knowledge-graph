"""
Test suite for Todoist export functionality
Run from project root: python3 tests/test_todoist_export.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.todoist_exporter import PRIORITY_MAP, export_to_todoist, TodoistExporter
from dataclasses import dataclass

@dataclass
class MockAction:
    id: str
    text: str
    priority: str
    source_tweet_id: str
    topic: str
    status: str
    created_at: str


def test_priority_mapping():
    """Verify priority mapping is correct"""
    assert PRIORITY_MAP['urgent'] == 4
    assert PRIORITY_MAP['high'] == 3
    assert PRIORITY_MAP['medium'] == 2
    assert PRIORITY_MAP['low'] == 1
    print("✓ Priority mapping correct")


def test_mock_export_single_action():
    """Test exporting a single action with mock API"""
    action = MockAction(
        id='1',
        text='Test todo',
        priority='high',
        source_tweet_id='123',
        topic='test',
        status='pending',
        created_at='2026-02-11'
    )
    
    result = export_to_todoist([action], api_token=None)
    
    assert result['success_count'] == 1
    assert result['failed_count'] == 0
    assert len(result['task_ids']) == 1
    assert result['task_ids'][0].startswith('mock_')
    print("✓ Single action export works")


def test_mock_export_multiple_actions():
    """Test exporting multiple actions with all priorities"""
    actions = [
        MockAction(
            id=str(i),
            text=f'Task {i}',
            priority=['urgent', 'high', 'medium', 'low'][i % 4],
            source_tweet_id=f'tweet_{i}',
            topic='test',
            status='pending',
            created_at='2026-02-11'
        )
        for i in range(5)
    ]
    
    result = export_to_todoist(actions, api_token=None)
    
    assert result['success_count'] == 5
    assert result['failed_count'] == 0
    assert len(result['task_ids']) == 5
    print("✓ Multiple action export works")


def test_auto_mock_mode_without_token():
    """Test that mock mode is auto-enabled without token"""
    exporter = TodoistExporter(api_token=None)
    assert exporter.use_mock == True
    print("✓ Auto mock mode works")


if __name__ == '__main__':
    test_priority_mapping()
    test_mock_export_single_action()
    test_mock_export_multiple_actions()
    test_auto_mock_mode_without_token()
    print("\n✅ All tests passed!")
