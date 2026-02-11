#!/usr/bin/env python3
"""Test Todoist export functionality"""
import sys
sys.path.insert(0, '/home/molty/.openclaw/workspace/projects/x-knowledge-graph/core')

from todoist_exporter import export_to_todoist, TodoistExporter

# Mock action for testing
class MockAction:
    def __init__(self, text, priority, topic="test", status="pending"):
        self.text = text
        self.priority = priority
        self.topic = topic
        self.status = status
        self.id = f"action_{hash(text) % 10000}"
        self.source_tweet_id = "12345"
        self.created_at = "2026-02-10T00:00:00"

# Test actions
actions = [
    MockAction("Buy milk", "high", "shopping"),
    MockAction("Call dentist", "urgent", "health"),
    MockAction("Email boss", "medium", "work"),
    MockAction("Water plants", "low", "home"),
]

print("Testing Todoist export with mock API...")
print("-" * 40)

# Test 1: export_to_todoist convenience function
result = export_to_todoist(actions, api_token=None)
print(f"export_to_todoist result: {result}")
assert result['success_count'] == 4, f"Expected 4 successes, got {result['success_count']}"
assert result['failed_count'] == 0, f"Expected 0 failures, got {result['failed_count']}"
assert len(result['task_ids']) == 4, f"Expected 4 task_ids"
print("✅ Test 1 passed: export_to_todoist works")

# Test 2: Priority mapping
print("\nTesting priority mapping:")
exporter = TodoistExporter(api_token=None, use_mock=True)

for priority, expected in [('urgent', 1), ('high', 2), ('medium', 3), ('low', 4)]:
    from todoist_exporter import PRIORITY_MAP
    actual = PRIORITY_MAP.get(priority)
    print(f"  {priority} -> p{5-actual} (internal: {actual})")
    assert actual == expected, f"Priority {priority} should map to {expected}, got {actual}"
print("✅ Test 2 passed: Priority mapping correct")

# Test 3: Mock failure handling
print("\nTesting failure handling...")
fail_result = export_to_todoist([MockAction("", "high")], api_token=None)
assert fail_result['failed_count'] == 1, "Empty content should fail"
print("✅ Test 3 passed: Failure handling works")

print("\n" + "=" * 40)
print("All tests passed! Todoist export is working.")
print("=" * 40)
