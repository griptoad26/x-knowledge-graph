"""Test Todoist Exporter with Mock API"""
import sys
import os

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from todoist_exporter import TodoistExporter, PRIORITY_MAP, export_to_todoist


# Mock ActionItem class for testing
class MockAction:
    def __init__(self, id, text, priority, source_tweet_id, topic, status, created_at):
        self.id = id
        self.text = text
        self.priority = priority
        self.source_tweet_id = source_tweet_id
        self.topic = topic
        self.status = status
        self.created_at = created_at


def test_priority_mapping():
    """Verify priority mapping is correct"""
    assert PRIORITY_MAP['urgent'] == 1, "urgent should map to p1 (Todoist p4)"
    assert PRIORITY_MAP['high'] == 2, "high should map to p2 (Todoist p3)"
    assert PRIORITY_MAP['medium'] == 3, "medium should map to p3 (Todoist p2)"
    assert PRIORITY_MAP['low'] == 4, "low should map to p4 (Todoist p1)"
    print("✅ Priority mapping verified")


def test_mock_export_single_action():
    """Test exporting a single action with mock API"""
    exporter = TodoistExporter(use_mock=True)
    
    action = MockAction(
        id="test-1",
        text="Buy wireless headphones on Amazon",
        priority="high",
        source_tweet_id="123456",
        topic="shopping",
        status="pending",
        created_at="2026-02-11"
    )
    
    result = exporter.export_action(action)
    
    assert result.success, f"Export should succeed with mock API: {result.error}"
    assert result.task_id, "Should have a task_id"
    assert result.task_id.startswith("mock_"), "Mock task_id should start with 'mock_'"
    print(f"✅ Single action exported: {result.task_id}")


def test_mock_export_multiple_actions():
    """Test exporting multiple actions"""
    actions = [
        MockAction("1", "Fix bug", "urgent", "111", "dev", "pending", "2026-02-11"),
        MockAction("2", "Review PR", "high", "222", "dev", "pending", "2026-02-10"),
        MockAction("3", "Update docs", "medium", "333", "docs", "pending", "2026-02-09"),
        MockAction("4", "Clean up", "low", "444", "admin", "pending", "2026-02-08"),
    ]
    
    exporter = TodoistExporter(use_mock=True)
    result = exporter.export_actions(actions)
    
    assert result['success_count'] == 4, f"Expected 4 successes, got {result['success_count']}"
    assert result['failed_count'] == 0, f"Expected 0 failures, got {result['failed_count']}"
    assert len(result['task_ids']) == 4, f"Expected 4 task_ids, got {len(result['task_ids'])}"
    print(f"✅ Multiple actions exported: {result['success_count']}/{result['total']}")


def test_convenience_function():
    """Test the export_to_todoist convenience function"""
    actions = [
        MockAction("1", "Test task", "medium", "111", "test", "pending", "2026-02-11"),
    ]
    
    # No API token = uses mock automatically
    result = export_to_todoist(actions)
    
    assert result['success_count'] == 1
    assert len(result['task_ids']) == 1
    print("✅ export_to_todoist convenience function works")


def test_priority_filter():
    """Test exporting with priority filter"""
    actions = [
        MockAction("1", "Urgent task", "urgent", "111", "test", "pending", "2026-02-11"),
        MockAction("2", "Low priority", "low", "222", "test", "pending", "2026-02-11"),
    ]
    
    exporter = TodoistExporter(use_mock=True)
    result = exporter.export_actions(actions, priority_filter=['urgent'])
    
    assert result['success_count'] == 1, f"Expected 1 urgent task, got {result['success_count']}"
    assert result['total'] == 1, f"Expected 1 total filtered, got {result['total']}"
    print("✅ Priority filter works")


def test_error_handling():
    """Test error handling for invalid content"""
    exporter = TodoistExporter(use_mock=True)
    
    # Empty content should fail
    class EmptyAction:
        text = ""
        priority = "medium"
        source_tweet_id = "123"
        topic = "test"
        status = "pending"
    
    result = exporter.export_action(EmptyAction())
    
    assert not result.success, "Empty content should fail"
    assert "invalid" in result.error.lower(), "Should report invalid content error"
    print("✅ Error handling works")


if __name__ == '__main__':
    print("Running Todoist Exporter Tests...\n")
    
    test_priority_mapping()
    test_mock_export_single_action()
    test_mock_export_multiple_actions()
    test_convenience_function()
    test_priority_filter()
    test_error_handling()
    
    print("\n🎉 All tests passed!")
