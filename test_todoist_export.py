#!/usr/bin/env python3
"""Test Todoist export functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.todoist_exporter import TodoistExporter, PRIORITY_MAP
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MockAction:
    id: str
    text: str
    priority: str
    source_tweet_id: str
    topic: str
    status: str
    created_at: str

# Test 1: Priority mapping
print("Test 1: Priority mapping...")
assert PRIORITY_MAP['urgent'] == 4, "urgent should be p4"
assert PRIORITY_MAP['high'] == 3, "high should be p3"
assert PRIORITY_MAP['medium'] == 2, "medium should be p2"
assert PRIORITY_MAP['low'] == 1, "low should be p1"
print("  ✓ Priority mapping correct")

# Test 2: Mock mode initialization
print("\nTest 2: Mock mode initialization...")
exporter = TodoistExporter(use_mock=True)
assert exporter.use_mock == True, "Should be in mock mode"
print("  ✓ Mock mode enabled")

# Test 3: Single action export
print("\nTest 3: Single action export...")
action = MockAction(
    id="test_1",
    text="Test action: Buy something on Amazon https://amzn.to/test123",
    priority="high",
    source_tweet_id="123456",
    topic="shopping",
    status="pending",
    created_at="2026-02-10"
)
result = exporter.export_action(action)
assert result.success == True, f"Export failed: {result.error}"
assert result.task_id.startswith("mock_"), f"Invalid task ID: {result.task_id}"
print(f"  ✓ Exported with task_id: {result.task_id}")

# Test 4: Multiple actions export
print("\nTest 4: Multiple actions export...")
actions = [
    MockAction(
        id=f"test_{i}",
        text=f"Action {i} with priority {p}",
        priority=p,
        source_tweet_id=str(1000+i),
        topic="test",
        status="pending",
        created_at="2026-02-10"
    )
    for i, p in enumerate(['urgent', 'high', 'medium', 'low'])
]
result = exporter.export_actions(actions)
assert result['success_count'] == 4, f"Expected 4 successes, got {result['success_count']}"
assert result['failed_count'] == 0, f"Expected 0 failures, got {result['failed_count']}"
print(f"  ✓ Exported {result['success_count']} actions")

# Test 5: Priority filter
print("\nTest 5: Priority filter...")
result = exporter.export_actions(actions, priority_filter=['urgent', 'high'])
assert result['success_count'] == 2, f"Expected 2 successes, got {result['success_count']}"
print(f"  ✓ Filtered to {result['success_count']} urgent/high actions")

# Test 6: Error handling
print("\nTest 6: Error handling...")
exporter.clear_mock_responses()
bad_action = MockAction(
    id="fail_1",
    text="",  # Empty content should fail
    priority="low",
    source_tweet_id="999",
    topic="test",
    status="pending",
    created_at="2026-02-10"
)
result = exporter.export_action(bad_action)
assert result.success == False, "Empty content should fail"
assert "invalid" in result.error.lower(), f"Expected invalid error, got: {result.error}"
print(f"  ✓ Correctly rejected empty content: {result.error}")

print("\n" + "=" * 50)
print("ALL TESTS PASSED ✓")
print("=" * 50)
