#!/usr/bin/env python3
"""
X Knowledge Graph - Test Suite
Quick validation that all modules load correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from src.data_ingestion import load_x_export, load_grok_export
        print("  ✓ data_ingestion")
    except Exception as e:
        print(f"  ✗ data_ingestion: {e}")
        return False
    
    try:
        from src.graph_builder import KnowledgeGraph
        print("  ✓ graph_builder")
    except Exception as e:
        print(f"  ✗ graph_builder: {e}")
        return False
    
    try:
        from src.action_extractor import ActionExtractor
        print("  ✓ action_extractor")
    except Exception as e:
        print(f"  ✗ action_extractor: {e}")
        return False
    
    try:
        from src.topic_modeler import TopicModeler
        print("  ✓ topic_modeler")
    except Exception as e:
        print(f"  ✗ topic_modeler: {e}")
        return False
    
    try:
        from src.task_flow import TaskFlowManager
        print("  ✓ task_flow")
    except Exception as e:
        print(f"  ✗ task_flow: {e}")
        return False
    
    return True

def test_graph_creation():
    """Test that we can create a graph"""
    print("\nTesting graph creation...")
    try:
        from src.graph_builder import KnowledgeGraph
        kg = KnowledgeGraph()
        kg.graph.add_node("test_node", type="test", text="Test content")
        stats = kg.get_stats()
        assert stats["total_nodes"] == 1
        print("  ✓ Graph creation works")
        return True
    except Exception as e:
        print(f"  ✗ Graph creation failed: {e}")
        return False

def test_action_extraction():
    """Test that action extraction works"""
    print("\nTesting action extraction...")
    try:
        from src.action_extractor import ActionExtractor
        extractor = ActionExtractor()
        
        # Test cases
        test_texts = [
            "TODO: fix this bug",
            "Need to update the documentation",
            "Follow up on the email",
            "Task: review PR #123",
            "Remember to call mom"
        ]
        
        actions = extractor.extract_actions_bulk(test_texts, "test")
        print(f"  ✓ Extracted {len(actions)} actions from 5 test texts")
        return len(actions) >= 3  # Should find at least 3 actions
    except Exception as e:
        print(f"  ✗ Action extraction failed: {e}")
        return False

def test_topic_modeling():
    """Test that topic modeling works"""
    print("\nTesting topic modeling...")
    try:
        from src.topic_modeler import TopicModeler
        modeler = TopicModeler()
        
        test_items = [
            {"text": "Python programming tutorial"},
            {"text": "JavaScript framework guide"},
            {"text": "Python machine learning"},
            {"text": "Web development tips"},
            {"text": "React JavaScript frontend"}
        ]
        
        topics = modeler.identify_topics(test_items)
        print(f"  ✓ Identified {len(topics)} topics from 5 items")
        return True
    except Exception as e:
        print(f"  ✗ Topic modeling failed: {e}")
        return False

def test_data_ingestion():
    """Test data loading (without actual files)"""
    print("\nTesting data ingestion module...")
    try:
        from src.data_ingestion import normalize_text
        
        # Test normalization - note: # is removed but text remains
        result1 = normalize_text("Hello @world #test")
        result2 = normalize_text("Check https://example.com")
        # Hashtags keep the word, just remove the #
        assert "Hello" in result1 and "test" in result1, f"Expected 'Hello test' in '{result1}'"
        assert result2 == "Check", f"Expected 'Check', got '{result2}'"
        print("  ✓ Text normalization works")
        return True
    except Exception as e:
        print(f"  ✗ Data ingestion failed: {e}")
        return False

def test_css_theme_variables():
    """Test that CSS theme variables are properly defined"""
    print("\nTesting CSS theme variables...")
    try:
        css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "frontend", "css", "layouts.css")
        with open(css_path, 'r') as f:
            css_content = f.read()

        # Check that :root contains all required dark theme variables
        dark_theme_vars = [
            '--bg-primary:', '--bg-secondary:', '--bg-tertiary:',
            '--text-primary:', '--text-secondary:',
            '--accent-primary:', '--accent-success:', '--accent-warning:', '--accent-danger:',
            '--border-color:', '--shadow:'
        ]
        for var in dark_theme_vars:
            assert var in css_content, f"Missing dark theme variable: {var}"

        # Check that [data-theme="light"] selector exists with complete theme variables
        assert '[data-theme="light"]' in css_content, "Missing [data-theme=\"light\"] selector"

        light_theme_vars = [
            '--bg-primary:', '--bg-secondary:', '--bg-tertiary:',
            '--text-primary:', '--text-secondary:',
            '--accent-primary:', '--accent-success:', '--accent-warning:', '--accent-danger:',
            '--border-color:', '--shadow:'
        ]
        for var in light_theme_vars:
            assert var in css_content, f"Missing light theme variable: {var}"

        # Check that light theme uses light background colors
        assert '#f5f5f5' in css_content, "Missing light theme bg-primary (#f5f5f5)"
        assert '#ffffff' in css_content, "Missing light theme bg-secondary (#ffffff)"

        # Check that light theme uses dark text colors
        assert '#1a1a2e' in css_content, "Missing light theme text-primary (#1a1a2e)"
        assert '#666' in css_content, "Missing light theme text-secondary (#666)"

        # Check that dark theme styles remain unchanged (dark colors present)
        assert '#1a1a2e' in css_content, "Missing dark theme bg-primary (#1a1a2e)"
        assert '#eee' in css_content, "Missing dark theme text-primary (#eee)"

        print("  ✓ CSS theme variables are properly defined")
        return True
    except Exception as e:
        print(f"  ✗ CSS theme variables test failed: {e}")
        return False

def test_theme_toggle_button():
    """Test that theme toggle button is properly defined in HTML"""
    print("\nTesting theme toggle button...")
    try:
        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "frontend", "index.html")
        with open(html_path, 'r') as f:
            html_content = f.read()

        # Check that theme toggle button exists
        assert 'id="theme-toggle"' in html_content, "Missing theme toggle button (id=\"theme-toggle\")"
        assert 'onclick="toggleTheme()"' in html_content, "Missing toggleTheme() onclick handler"

        # Check that theme icon exists
        assert 'id="theme-icon"' in html_content, "Missing theme icon (id=\"theme-icon\")"

        # Check that button has accessibility attributes
        assert 'aria-label="Toggle theme"' in html_content, "Missing aria-label for accessibility"
        assert 'title="Switch to light/dark theme"' in html_content, "Missing title attribute"

        # Check that button is in header-actions container
        assert 'class="header-actions"' in html_content or 'class=\\"header-actions\\"' in html_content, \
            "Theme toggle not in header-actions"

        # Check that JavaScript functions exist
        assert 'function toggleTheme()' in html_content, "Missing toggleTheme() function"
        assert 'function applyTheme()' in html_content, "Missing applyTheme() function"
        assert 'function loadThemePreference()' in html_content, "Missing loadThemePreference() function"
        assert 'function saveThemePreference()' in html_content, "Missing saveThemePreference() function"

        # Check that theme initialization is called
        assert 'loadThemePreference()' in html_content, "Missing loadThemePreference() initialization call"

        # Check that CSS button styles exist
        css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "frontend", "css", "layouts.css")
        with open(css_path, 'r') as f:
            css_content = f.read()

        assert '.btn-theme' in css_content, "Missing .btn-theme CSS class"
        assert 'btn-theme:hover' in css_content or '.btn-theme:hover' in css_content, \
            "Missing .btn-theme:hover CSS class"

        print("  ✓ Theme toggle button is properly defined")
        return True
    except Exception as e:
        print(f"  ✗ Theme toggle button test failed: {e}")
        return False

def test_help_modal_theme_docs():
    """Test that help modal contains theme documentation"""
    print("\nTesting help modal theme documentation...")
    try:
        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "frontend", "index.html")
        with open(html_path, 'r') as f:
            html_content = f.read()

        # Check that help modal exists
        assert 'id="help-modal"' in html_content, "Missing help modal (id=\"help-modal\")"

        # Check that theme documentation exists in help modal
        assert 'Light/Dark Mode' in html_content, "Missing 'Light/Dark Mode' section in help modal"
        assert 'Theme Toggle:' in html_content, "Missing 'Theme Toggle' documentation"
        assert 'Auto-detection:' in html_content, "Missing 'Auto-detection' documentation"
        assert 'Persistence:' in html_content, "Missing 'Persistence' documentation"

        # Check that theme documentation is in the help modal section (not elsewhere)
        # Find the help modal section and verify theme docs are inside
        help_start = html_content.find('id="help-modal"')
        help_end = html_content.find('</script>', help_start)  # Find script tag after modal
        help_section = html_content[help_start:help_end]

        assert 'Light/Dark Mode' in help_section, "Theme documentation not in help modal"
        assert 'Theme Toggle:' in help_section, "Theme Toggle docs not in help modal"
        assert 'Auto-detection:' in help_section, "Auto-detection docs not in help modal"
        assert 'Persistence:' in help_section, "Persistence docs not in help modal"

        print("  ✓ Help modal contains theme documentation")
        return True
    except Exception as e:
        print(f"  ✗ Help modal theme docs test failed: {e}")
        return False

def main():
    print("=" * 50)
    print("X Knowledge Graph - Test Suite")
    print("=" * 50)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Graph Creation", test_graph_creation()))
    results.append(("Action Extraction", test_action_extraction()))
    results.append(("Topic Modeling", test_topic_modeling()))
    results.append(("Data Ingestion", test_data_ingestion()))
    results.append(("CSS Theme Variables", test_css_theme_variables()))
    results.append(("Theme Toggle Button", test_theme_toggle_button()))
    results.append(("Help Modal Theme Docs", test_help_modal_theme_docs()))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    
    passed = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Application is ready.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
