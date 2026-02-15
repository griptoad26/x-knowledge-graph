"""
Pytest configuration for X Knowledge Graph tests
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "core"))

# Set test data paths
os.environ['TEST_DATA_DIR'] = str(PROJECT_ROOT / "test_data")

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
