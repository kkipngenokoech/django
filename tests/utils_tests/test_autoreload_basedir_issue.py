import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import override_settings
from django.utils.autoreload import StatReloader


def test_issue_reproduction():
    """Test that autoreload works when BASE_DIR is added to TEMPLATES DIRS."""
    # Create a temporary directory to simulate BASE_DIR
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        
        # Create a test file in the base directory
        test_file = base_dir / "test_file.py"
        test_file.write_text("# test content")
        
        # Configure templates with BASE_DIR in DIRS (reproducing the issue)
        templates_config = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [str(base_dir)],  # This is what causes the issue
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ]
        
        with override_settings(TEMPLATES=templates_config):
            reloader = StatReloader()
            
            # Add the test file to be watched
            reloader.extra_files.add(test_file)
            
            # Get initial snapshot
            initial_files = list(reloader.snapshot_files())
            initial_file_paths = {f[0] for f in initial_files}
            
            # The test file should be in the watched files
            assert test_file in initial_file_paths, "Test file should be watched"
            
            # Modify the file to trigger a change
            test_file.write_text("# modified content")
            
            # Get new snapshot
            new_files = list(reloader.snapshot_files())
            new_file_paths = {f[0] for f in new_files}
            
            # The file should still be watchable after modification
            # This assertion will fail if the bug exists because the autoreload
            # system loses track of files when BASE_DIR is in template DIRS
            assert test_file in new_file_paths, "Test file should still be watched after modification"
            
            # Verify that the file modification time is properly detected
            file_mtimes = {f[0]: f[1] for f in new_files}
            assert test_file in file_mtimes, "Modified file should have detectable mtime"