"""Test Todoist exporter mock mode"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.todoist_exporter import TodoistExporter, export_to_todoist, PRIORITY_MAP

# Create mock action class
class MockAction:
    def __init__(self, text, priority, source_tweet_id, topic='test', status='pending', created_at='2026-02-11'):
        self.id = f"action_{hash(text) % 10000}"
        self.text = text
        self.priority = priority
        self.source_tweet_id = source_tweet_id
        self.topic = topic
        self.status = status
        self.created_at = created_at

# Test priority mapping
print("Priority mapping:", PRIORITY_MAP)
assert PRIORITY_MAP['urgent'] == 4
assert PRIORITY_MAP['high'] == 3
assert PRIORITY_MAP['medium'] == 2
assert PRIORITY_MAP['low'] == 1
print("✓ Priority mapping correct")

# Test mock export
actions = [
    MockAction("Test urgent task", "urgent", "12345"),
    MockAction("Test high priority", "high", "12346"),
    MockAction("Test medium task", "medium", "12347"),
    MockAction("Test low priority", "low", "12348"),
]

# Use mock mode (no token)
result = export_to_todoist(actions, api_token=None)
print(f"Export result: {result}")
assert result['success_count'] == 4
assert result['failed_count'] == 0
assert len(result['task_ids']) == 4
print("✓ Mock export works")

# Test TodoistExporter directly
exporter = TodoistExporter(api_token=None, use_mock=True)
single_result = exporter.export_action(actions[0])
assert single_result.success
assert single_result.task_id.startswith('mock_')
print(f"✓ Single export: {single_result}")

print("\n✅ All tests passed!")
