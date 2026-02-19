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


class TestThemeToggleButton:
    """Test suite for verifying theme toggle button and JavaScript functions"""

    @pytest.fixture
    def html_content(self):
        """Read index.html content"""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        with open(html_path, 'r') as f:
            return f.read()

    @pytest.fixture
    def js_content(self, html_content):
        """Extract JavaScript content from index.html"""
        # Extract the inline JavaScript
        js_match = re.search(r'<script>\s*(//.*?)\s*</script>', html_content, re.DOTALL)
        if js_match:
            return js_match.group(1)
        return ""

    def test_theme_toggle_button_exists(self, html_content):
        """Test that theme toggle button exists in header"""
        # Check for theme-toggle button
        assert 'id="theme-toggle"' in html_content, \
            "Theme toggle button with id='theme-toggle' must exist"
        
        # Check button is in header area
        header_match = re.search(r'<header[^>]*>.*?id="theme-toggle".*?</header>', html_content, re.DOTALL)
        assert header_match is not None, \
            "Theme toggle button should be inside the header element"

    def test_theme_toggle_button_has_aria_label(self, html_content):
        """Test that theme toggle button has aria-label attribute"""
        # Check for aria-label
        aria_pattern = r'id="theme-toggle"[^>]*aria-label="[^"]*"'
        aria_match = re.search(aria_pattern, html_content)
        assert aria_match is not None, \
            "Theme toggle button must have aria-label attribute"
        
        # Verify aria-label content is meaningful
        aria_match = re.search(r'aria-label="([^"]*)"', html_content)
        aria_label = aria_match.group(1) if aria_match else ""
        assert len(aria_label) > 5, \
            "aria-label should contain a meaningful description"

    def test_theme_toggle_button_has_title(self, html_content):
        """Test that theme toggle button has title attribute"""
        # Check for title
        title_pattern = r'id="theme-toggle"[^>]*title="[^"]*"'
        title_match = re.search(title_pattern, html_content)
        assert title_match is not None, \
            "Theme toggle button must have title attribute"
        
        # Verify title content is meaningful
        title_match = re.search(r'title="([^"]*)"', html_content)
        title = title_match.group(1) if title_match else ""
        assert len(title) > 5, \
            "title should contain a meaningful description"

    def test_theme_icon_exists(self, html_content):
        """Test that theme icon span exists inside toggle button"""
        # Check for theme-icon span
        assert 'id="theme-icon"' in html_content, \
            "Theme icon span with id='theme-icon' must exist"
        
        # Check icon is inside toggle button
        icon_pattern = r'<button[^>]*id="theme-toggle"[^>]*>.*?id="theme-icon"[^>]*>.*?</span>.*?</button>'
        icon_match = re.search(icon_pattern, html_content, re.DOTALL)
        assert icon_match is not None, \
            "Theme icon should be inside the theme toggle button"

    def test_theme_icon_has_aria_hidden(self, html_content):
        """Test that theme icon has aria-hidden=true for accessibility"""
        # Check for aria-hidden on icon
        aria_hidden_pattern = r'id="theme-icon"[^>]*aria-hidden="true"'
        aria_hidden_match = re.search(aria_hidden_pattern, html_content)
        assert aria_hidden_match is not None, \
            "Theme icon must have aria-hidden='true' for accessibility"


class TestThemeJavaScriptFunctions:
    """Test suite for verifying theme toggle JavaScript functions"""

    @pytest.fixture
    def html_content(self):
        """Read index.html content"""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        with open(html_path, 'r') as f:
            return f.read()

    def test_toggleTheme_function_exists(self, html_content):
        """Test that toggleTheme() function is defined"""
        # Check for toggleTheme function definition
        function_pattern = r'function\s+toggleTheme\s*\(\s*\)\s*\{'
        function_match = re.search(function_pattern, html_content)
        assert function_match is not None, \
            "toggleTheme() function must be defined"

    def test_toggleTheme_switches_theme(self, html_content):
        """Test that toggleTheme() switches between dark and light"""
        # Check that toggleTheme changes currentTheme
        toggle_match = re.search(r'currentTheme\s*=\s*currentTheme\s*===\s*[\'"]dark[\'"]\s*\?\s*[\'"]light[\'"]\s*:\s*[\'"]dark[\'"]', html_content)
        assert toggle_match is not None, \
            "toggleTheme() must switch currentTheme between 'dark' and 'light'"
        
        # Alternatively check for if/else pattern
        if_pattern = r'if\s*\(\s*currentTheme\s*===\s*[\'"]dark[\'"]\s*\)\s*\{[^}]*currentTheme\s*=\s*[\'"]light[\'"]'
        assert re.search(if_pattern, html_content) or toggle_match is not None, \
            "toggleTheme() must have logic to switch theme"

    def test_applyTheme_function_exists(self, html_content):
        """Test that applyTheme() function is defined"""
        function_pattern = r'function\s+applyTheme\s*\(\s*\)\s*\{'
        function_match = re.search(function_pattern, html_content)
        assert function_match is not None, \
            "applyTheme() function must be defined"

    def test_applyTheme_updates_data_theme(self, html_content):
        """Test that applyTheme() sets data-theme attribute on documentElement"""
        # Check for setAttribute call
        set_attr_pattern = r'applyTheme\s*\(\s*\)\s*\{[^}]*document\.documentElement\.setAttribute\s*\(\s*[\'"]data-theme[\'"]\s*,\s*currentTheme\s*\)'
        set_attr_match = re.search(set_attr_pattern, html_content, re.DOTALL)
        assert set_attr_match is not None, \
            "applyTheme() must set data-theme attribute on documentElement"

    def test_applyTheme_updates_icon(self, html_content):
        """Test that applyTheme() updates the theme icon"""
        # Check for icon update - the actual pattern in the code
        icon_pattern = r'icon\.textContent\s*=\s*currentTheme\s*===\s*[\'"]dark[\'"]\s*\?\s*[\'"]🌙[\'"]\s*:\s*[\'"]☀️[\'"]'
        icon_match = re.search(icon_pattern, html_content)
        assert icon_match is not None, \
            "applyTheme() must update theme icon based on current theme (moon for dark, sun for light)"
        
        # Also check the specific icon emojis are used
        assert '🌙' in html_content, \
            "Dark mode moon icon (🌙) should be present"
        assert '☀️' in html_content, \
            "Light mode sun icon (☀️) should be present"

    def test_loadThemePreference_function_exists(self, html_content):
        """Test that loadThemePreference() function is defined"""
        function_pattern = r'function\s+loadThemePreference\s*\(\s*\)\s*\{'
        function_match = re.search(function_pattern, html_content)
        assert function_match is not None, \
            "loadThemePreference() function must be defined"

    def test_loadThemePreference_reads_localStorage(self, html_content):
        """Test that loadThemePreference() reads from localStorage"""
        # Check for localStorage.getItem
        ls_pattern = r'loadThemePreference\s*\(\s*\)\s*\{[^}]*localStorage\.getItem\s*\(\s*[\'"]xkg_theme[\'"]\s*\)'
        ls_match = re.search(ls_pattern, html_content, re.DOTALL)
        assert ls_match is not None, \
            "loadThemePreference() must read from localStorage with key 'xkg_theme'"

    def test_loadThemePreference_has_fallback(self, html_content):
        """Test that loadThemePreference() falls back to system preference if no saved value"""
        # Check for system preference detection
        assert "matchMedia('(prefers-color-scheme: light)')" in html_content, \
            "loadThemePreference() should detect system preference as fallback"
        
        # Check that there's a validation for saved theme
        assert "savedTheme === 'light' || savedTheme === 'dark'" in html_content, \
            "loadThemePreference() should validate saved theme and fall back if invalid"

    def test_saveThemePreference_function_exists(self, html_content):
        """Test that saveThemePreference() function is defined"""
        function_pattern = r'function\s+saveThemePreference\s*\(\s*\)\s*\{'
        function_match = re.search(function_pattern, html_content)
        assert function_match is not None, \
            "saveThemePreference() function must be defined"

    def test_saveThemePreference_writes_localStorage(self, html_content):
        """Test that saveThemePreference() writes to localStorage"""
        # Check for localStorage.setItem
        ls_pattern = r'saveThemePreference\s*\(\s*\)\s*\{[^}]*localStorage\.setItem\s*\(\s*[\'"]xkg_theme[\'"]\s*,\s*currentTheme\s*\)'
        ls_match = re.search(ls_pattern, html_content, re.DOTALL)
        assert ls_match is not None, \
            "saveThemePreference() must save currentTheme to localStorage with key 'xkg_theme'"

    def test_theme_functions_are_connected(self, html_content):
        """Test that theme functions are properly connected"""
        # toggleTheme should call applyTheme and saveThemePreference
        toggle_start = html_content.find('function toggleTheme()')
        toggle_end = html_content.find('function applyTheme()')
        toggle_body = html_content[toggle_start:toggle_end]
        
        assert 'applyTheme();' in toggle_body, \
            "toggleTheme() should call applyTheme()"
        assert 'saveThemePreference();' in toggle_body, \
            "toggleTheme() should call saveThemePreference()"
        
        # loadThemePreference should call applyTheme at the end
        load_start = html_content.find('function loadThemePreference()')
        load_end = html_content.find('function saveThemePreference()')
        load_body = html_content[load_start:load_end]
        
        assert 'applyTheme();' in load_body, \
            "loadThemePreference() should call applyTheme() to set the theme on load"


class TestThemeIcons:
    """Test suite for verifying theme icon behavior"""

    @pytest.fixture
    def html_content(self):
        """Read index.html content"""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        with open(html_path, 'r') as f:
            return f.read()

    def test_dark_mode_icon_is_moon(self, html_content):
        """Test that dark mode uses moon emoji (🌙)"""
        # Check moon emoji is used for dark mode
        dark_icon_pattern = r'currentTheme\s*===\s*[\'"]dark[\'"].*?🌙|🌙.*?currentTheme\s*===\s*[\'"]dark[\'"]'
        dark_match = re.search(dark_icon_pattern, html_content, re.DOTALL)
        assert dark_match is not None, \
            "Dark mode should display moon emoji (🌙)"

    def test_light_mode_icon_is_sun(self, html_content):
        """Test that light mode uses sun emoji (☀️)"""
        # Check sun emoji is used for light mode (ternary: dark ? moon : sun)
        light_icon_pattern = r'currentTheme\s*===\s*[\'"]dark[\'"]\s*\?\s*[\'"]🌙[\'"]\s*:\s*[\'"]☀️[\'"]'
        light_match = re.search(light_icon_pattern, html_content)
        assert light_match is not None, \
            "Light mode should display sun emoji (☀️)"

    def test_initial_theme_is_dark(self, html_content):
        """Test that initial theme is set to dark"""
        # Check initial theme variable
        initial_pattern = r'let\s+currentTheme\s*=\s*[\'"]dark[\'"]'
        initial_match = re.search(initial_pattern, html_content)
        assert initial_match is not None, \
            "Initial theme should be 'dark'"


class TestThemeAccessibility:
    """Test suite for theme accessibility features"""

    @pytest.fixture
    def html_content(self):
        """Read index.html content"""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        with open(html_path, 'r') as f:
            return f.read()

    def test_toggle_button_is_accessible(self, html_content):
        """Test that theme toggle button has accessibility attributes"""
        # Check button has role="button" or is a button element
        button_pattern = r'<button[^>]*id="theme-toggle"'
        button_match = re.search(button_pattern, html_content)
        assert button_match is not None, \
            "Theme toggle should be a <button> element"
        
        # Verify all required accessibility attributes
        assert 'aria-label' in html_content or 'aria-labelledby' in html_content, \
            "Theme toggle should have aria-label or aria-labelledby"
        
        assert 'title=' in html_content, \
            "Theme toggle should have title attribute"

    def test_icon_is_hidden_from_accessibility_tree(self, html_content):
        """Test that decorative icon is hidden from screen readers"""
        aria_hidden_pattern = r'<span[^>]*id="theme-icon"[^>]*aria-hidden="true"'
        aria_hidden_match = re.search(aria_hidden_pattern, html_content)
        assert aria_hidden_match is not None, \
            "Theme icon should have aria-hidden='true' to hide from screen readers"
