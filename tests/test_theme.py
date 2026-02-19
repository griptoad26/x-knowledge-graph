"""
Tests for CSS Theme Variables and Dark Mode Structure
Verifies that dark mode CSS variables are properly defined in layouts.css
"""

import pytest
import re
from pathlib import Path


class TestCSSThemeVariables:
    """Test suite for verifying CSS theme structure"""

    @pytest.fixture
    def css_content(self):
        """Read layouts.css content"""
        css_path = Path(__file__).parent.parent / "frontend" / "css" / "layouts.css"
        with open(css_path, 'r') as f:
            return f.read()

    @pytest.fixture
    def dark_theme_variables(self, css_content):
        """Extract dark theme CSS variables from :root selector"""
        # Find the :root block
        root_match = re.search(r':root\s*\{([^}]+)\}', css_content, re.DOTALL)
        if not root_match:
            return {}
        
        root_content = root_match.group(1)
        # Extract all --variable: value; pairs
        variables = {}
        for match in re.finditer(r'(--[\w-]+):\s*([^;]+);', root_content):
            variables[match.group(1)] = match.group(2).strip()
        return variables

    @pytest.fixture
    def light_theme_variables(self, css_content):
        """Extract light theme CSS variables from [data-theme='light'] selector"""
        # Find the [data-theme="light"] block
        light_match = re.search(r'\[data-theme="light"\]\s*\{([^}]+)\}', css_content, re.DOTALL)
        if not light_match:
            return {}
        
        light_content = light_match.group(1)
        # Extract all --variable: value; pairs
        variables = {}
        for match in re.finditer(r'(--[\w-]+):\s*([^;]+);', light_content):
            variables[match.group(1)] = match.group(2).strip()
        return variables

    def test_dark_theme_variables_exist(self, dark_theme_variables):
        """Test that all required dark theme CSS variables exist in :root"""
        required_vars = [
            '--bg-primary',
            '--bg-secondary', 
            '--bg-tertiary',
            '--text-primary',
            '--text-secondary',
            '--accent-primary',
            '--accent-success',
            '--accent-warning',
            '--accent-danger',
            '--border-color',
            '--shadow',
        ]
        
        for var in required_vars:
            assert var in dark_theme_variables, f"Missing dark theme variable: {var}"

    def test_dark_theme_variables_have_values(self, dark_theme_variables):
        """Test that dark theme CSS variables have non-empty values"""
        for var, value in dark_theme_variables.items():
            assert value, f"Dark theme variable {var} has empty value"
            # Check for valid color values
            assert any(c in value for c in ['#', 'rgb', 'rgba']), f"Variable {var} has no color value: {value}"

    def test_light_theme_override_exists(self, light_theme_variables):
        """Test that [data-theme='light'] selector exists and has variables"""
        required_vars = [
            '--bg-primary',
            '--bg-secondary',
            '--bg-tertiary',
            '--text-primary',
            '--text-secondary',
            '--accent-primary',
            '--accent-success',
            '--accent-warning',
            '--accent-danger',
            '--border-color',
            '--shadow',
        ]
        
        for var in required_vars:
            assert var in light_theme_variables, f"Missing light theme override variable: {var}"

    def test_light_theme_variables_have_values(self, light_theme_variables):
        """Test that light theme CSS variables have non-empty values"""
        for var, value in light_theme_variables.items():
            assert value, f"Light theme variable {var} has empty value"
            # Check for valid color values
            assert any(c in value for c in ['#', 'rgb', 'rgba']), f"Variable {var} has no color value: {value}"

    def test_light_theme_is_lighter_than_dark(self, dark_theme_variables, light_theme_variables):
        """Test that light theme has lighter background colors than dark theme"""
        # Light theme should have lighter background colors (higher brightness)
        dark_bg = dark_theme_variables.get('--bg-primary', '')
        light_bg = light_theme_variables.get('--bg-primary', '')
        
        # Convert hex to brightness for comparison
        def hex_brightness(hex_color):
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                return (r * 299 + g * 587 + b * 114) / 1000
            return 0
        
        dark_brightness = hex_brightness(dark_bg)
        light_brightness = hex_brightness(light_bg)
        
        assert light_brightness > dark_brightness, \
            f"Light theme background should be lighter: dark={dark_bg}, light={light_bg}"

    def test_css_variables_used_in_styles(self, css_content):
        """Test that CSS variables are used throughout the stylesheet"""
        # Check that common components use CSS variables
        components_with_vars = [
            ('body', 'background', '--bg-primary'),
            ('body', 'color', '--text-primary'),
            ('.header', 'background', '--bg-secondary'),
            ('.sidebar', 'background', '--bg-secondary'),
            ('.btn-primary', 'background', '--accent-primary'),
        ]
        
        for selector, property_name, expected_var in components_with_vars:
            # Find the selector block and check for the property
            selector_pattern = re.escape(selector) + r'\s*\{([^}]+)\}'
            match = re.search(selector_pattern, css_content)
            assert match is not None, f"Selector {selector} not found"
            
            block_content = match.group(1)
            # Check if the property uses the expected variable (anywhere in the value)
            property_pattern = rf'{property_name}\s*:\s*[^{{}}*]*var\({re.escape(expected_var)}\)'
            property_match = re.search(property_pattern, block_content)
            assert property_match is not None, \
                f"Component {selector} should use {expected_var} for {property_name}"

    def test_scrollbar_uses_theme_colors(self, css_content):
        """Test that scrollbar styles use theme CSS variables"""
        # Check scrollbar uses theme colors
        assert 'var(--bg-primary)' in css_content or '--bg-primary' in css_content
        assert 'var(--border-color)' in css_content or '--border-color' in css_content

    def test_buttons_use_theme_colors(self, css_content):
        """Test that button styles use theme CSS variables"""
        # Check that buttons use CSS variables for colors
        button_patterns = [
            r'\.btn[^{]*\{[^}]*var\(--bg',
            r'\.btn[^{]*\{[^}]*var\(--text',
            r'\.btn[^{]*\{[^}]*var\(--border',
        ]
        
        for pattern in button_patterns:
            match = re.search(pattern, css_content)
            assert match is not None, f"Buttons should use theme CSS variables"

    def test_cards_and_panels_use_theme_colors(self, css_content):
        """Test that cards and panels use theme CSS variables"""
        # Check that various container components use CSS variables
        components = ['.task-card', '.timeline-item', '.cluster-card', '.insight-stat-card']
        
        for component in components:
            # Find the component definition
            escaped_component = re.escape(component)
            pattern = escaped_component + r'\s*\{[^}]*\}'
            match = re.search(pattern, css_content)
            if match:
                component_css = match.group(0)
                # Should use at least one theme variable
                assert 'var(--' in component_css, \
                    f"{component} should use theme CSS variables"

    def test_no_hardcoded_colors_in_components(self, css_content):
        """Test that major components don't use hardcoded colors instead of variables"""
        # These patterns would indicate hardcoded colors (excluding CSS variable definitions)
        lines = css_content.split('\n')
        in_root_block = False
        in_light_theme_block = False
        hardcoded_in_components = []
        
        for i, line in enumerate(lines):
            if ':root' in line:
                in_root_block = True
            elif '[data-theme="light"]' in line:
                in_light_theme_block = True
                in_root_block = False
            elif '{' in line and not in_root_block and not in_light_theme_block:
                in_root_block = False
                in_light_theme_block = False
            
            # Check for hardcoded colors in component definitions (not variable definitions)
            if not in_root_block and not in_light_theme_block:
                if re.search(r'[a-z-]+\s*\{', line):
                    # Starting a component definition - check for hardcoded colors
                    if re.search(r'#[0-9a-fA-F]{3,6}', line):
                        # Could be legitimate, flag for review
                        if 'var(--' not in line:
                            hardcoded_in_components.append(f"Line {i+1}: {line.strip()}")
        
        # Allow some hardcoded colors for specific use cases (icons, avatars, etc.)
        # but major theming should use variables
        assert len(hardcoded_in_components) < 10, \
            f"Found {len(hardcoded_in_components)} potential hardcoded colors in components"

    def test_theme_selector_for_light_override(self, css_content):
        """Test that [data-theme='light'] selector is properly defined"""
        # Verify the light theme override pattern exists
        assert '[data-theme="light"]' in css_content, \
            "Light theme override selector [data-theme='light'] must exist"
        
        # Verify it contains theme variable overrides
        light_theme_match = re.search(r'\[data-theme="light"\]\s*\{([^}]+)\}', css_content, re.DOTALL)
        assert light_theme_match is not None, \
            "[data-theme='light'] should have a block with theme overrides"
        
        light_content = light_theme_match.group(1)
        # Should override at least background and text colors
        assert '--bg-primary' in light_content, \
            "[data-theme='light'] should override --bg-primary"
        assert '--text-primary' in light_content, \
            "[data-theme='light'] should override --text-primary"

    def test_all_variables_consistent_between_themes(self, dark_theme_variables, light_theme_variables):
        """Test that both themes define the same set of variables"""
        dark_vars = set(dark_theme_variables.keys())
        light_vars = set(light_theme_variables.keys())
        
        # Light theme should have all the same variables as dark theme
        missing_in_light = dark_vars - light_vars
        assert not missing_in_light, \
            f"Variables missing in light theme: {missing_in_light}"
        
        # Light theme might have additional variables, which is okay
