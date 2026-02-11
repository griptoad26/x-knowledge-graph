#!/usr/bin/env python3
"""Test Todoist exporter with mock API"""
import sys
sys.path.insert(0, '/home/molty/.openclaw/workspace/projects/x-knowledge-graph')

from core.todoist_exporter import TodoistExporter, export_to_todoist, PRIORITY_MAP

# Mock ActionItem class for testing
class MockAction:
    def __init__(self, text, priority='medium', source_tweet_id='123', topic='test', status='pending'):
        self.text = text
        self.priority = priority
        self.source_tweet_id = source_tweet_id
        self.topic = topic
        self.status = status
        self.created_at = '2026-02-10'
        self.id = f'action_{hash(text) % 10000}'

# Test priority mapping
print("Priority mapping:", PRIORITY_MAP)
assert PRIORITY_MAP['urgent'] == 1, "urgent should map to 1"
assert PRIORITY_MAP['high'] == 2, "high should map to 2"
assert PRIORITY_MAP['medium'] == 3, "medium should map to 3"
assert PRIORITY_MAP['low'] == 4, "low should map to 4"
print("✓ Priority mapping correct")

# Test mock API
print("\nTesting mock API...")

exporter = TodoistExporter(use_mock=True)
assert exporter.use_mock == True, "Mock mode should be enabled"

# Test single action export
action = MockAction("Test action", priority="urgent")
result = exporter.export_action(action)
print(f"Single export result: {result}")
assert result.success == True, "Mock export should succeed"
assert result.task_id is not None, "Should have mock task_id"
print("✓ Single action export works")

# Test batch export
actions = [
    MockAction("Action 1", priority="high"),
    MockAction("Action 2", priority="medium"),
    MockAction("Action 3", priority="low"),
]

batch_result = exporter.export_actions(actions)
print(f"Batch export result: {batch_result}")
assert batch_result['success_count'] == 3, "All 3 should succeed"
assert batch_result['failed_count'] == 0, "None should fail"
assert len(batch_result['task_ids']) == 3, "Should have 3 task_ids"
print("✓ Batch export works")

# Test convenience function (no token = mock mode)
print("\nTesting export_to_todoist convenience function...")
result = export_to_todoist(actions)  # No token = mock mode
print(f"Result: {result}")
assert result['success_count'] == 3
print("✓ export_to_todoist works")

print("\n✅ All tests passed!")
