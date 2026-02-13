#!/usr/bin/env python3
"""Test Todoist export with mock API"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.todoist_exporter import export_to_todoist, PRIORITY_MAP

# Mock action class
class MockAction:
    def __init__(self, text, priority, topic='test', status='pending', source_tweet_id='123'):
        self.text = text
        self.priority = priority
        self.topic = topic
        self.status = status
        self.source_tweet_id = source_tweet_id
        self.created_at = '2026-02-12'

# Test cases
actions = [
    MockAction("Fix critical bug", "urgent"),
    MockAction("Review PR", "high"),
    MockAction("Update docs", "medium"),
    MockAction("Clean up old files", "low"),
]

print("Testing Todoist Export (mock mode)...")
print(f"Priority mapping: {PRIORITY_MAP}")

result = export_to_todoist(actions, api_token=None)  # Mock mode

print(f"\nResults:")
print(f"  Success: {result['success_count']}")
print(f"  Failed: {result['failed_count']}")
print(f"  Task IDs: {result.get('task_ids', [])}")

if result['success_count'] > 0:
    print("\n✅ Todoist export working!")
else:
    print("\n❌ Export failed")
    sys.exit(1)
