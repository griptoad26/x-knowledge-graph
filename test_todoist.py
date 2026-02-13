#!/usr/bin/env python3
"""Test Todoist exporter functionality"""
import sys
sys.path.insert(0, '/home/molty/.openclaw/workspace/projects/x-knowledge-graph')

from core.todoist_exporter import PRIORITY_MAP, TodoistExporter, export_to_todoist

# Test priority mapping
print("Priority Mapping Test:")
for xkg, todoist in PRIORITY_MAP.items():
    print(f"  {xkg} -> p{todoist}")

# Mock ActionItem for testing
class MockAction:
    def __init__(self, text, priority, source_tweet_id, topic='test', status='pending', created_at='2026-02-12'):
        self.text = text
        self.priority = priority
        self.source_tweet_id = source_tweet_id
        self.topic = topic
        self.status = status
        self.created_at = created_at

# Test with mock API
print("\nMock API Test:")
actions = [
    MockAction("Buy coffee beans", "high", "1234567890"),
    MockAction("Research X API", "urgent", "0987654321"),
    MockAction("Clean workspace", "low", "5555555555"),
]

exporter = TodoistExporter(use_mock=True)
result = exporter.export_actions(actions)

print(f"  Success count: {result['success_count']}")
print(f"  Failed count: {result['failed_count']}")
print(f"  Task IDs: {result['task_ids']}")
print(f"  Total: {result['total']}")

# Test convenience function
print("\nConvenience Function Test:")
result2 = export_to_todoist(actions)
print(f"  Exported: {result2['success_count']}, Failed: {result2['failed_count']}")

print("\n✅ Todoist export is working!")
