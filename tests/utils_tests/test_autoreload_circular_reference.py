import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from django.utils.autoreload import WatchmanReloader, StatReloader, common_roots


def test_issue_reproduction():
    """Test that adding BASE_DIR to template dirs causes autoreload issues."""
    # Create a temporary project structure
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        settings_file = base_dir / 'settings.py'
        templates_dir = base_dir / 'templates'
        
        # Create the settings file and templates directory
        settings_file.write_text('# settings file')
        templates_dir.mkdir()
        
        # Simulate the problematic scenario where BASE_DIR is added to TEMPLATES DIRS
        # This creates a circular reference where the autoreload system watches
        # the project root directory which contains the settings file
        
        # Create a reloader instance
        reloader = StatReloader()
        
        # Add the base directory to be watched (simulating BASE_DIR in TEMPLATES DIRS)
        reloader.watch_dir(base_dir, '*.py')
        
        # Get the watched files - this should include the settings file
        watched_files = list(reloader.watched_files())
        watched_paths = [Path(f) for f in watched_files]
        
        # The issue: when BASE_DIR is in template dirs, the autoreload system
        # tries to watch the entire project root, creating a circular dependency
        # This manifests as the common_roots function returning overly broad paths
        roots = common_roots(watched_paths + [base_dir])
        
        # The bug: common_roots should not return the base directory itself
        # when it contains the settings file, as this creates infinite recursion
        # in the file watching system
        
        # This assertion will FAIL on the current buggy code because
        # common_roots doesn't handle the circular reference properly
        assert base_dir not in roots, f"BASE_DIR {base_dir} should not be in common roots {roots} to avoid circular reference"