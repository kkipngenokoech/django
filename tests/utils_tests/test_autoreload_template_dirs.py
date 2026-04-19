import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings
from django.utils.autoreload import BaseReloader, get_reloader
from django.template import engines


def test_issue_reproduction():
    """Test that autoreload works when BASE_DIR is added to TEMPLATES DIRS."""
    # Create a temporary directory structure similar to a Django project
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        templates_dir = base_dir / 'templates'
        templates_dir.mkdir()
        
        # Create a test file to watch
        test_file = base_dir / 'test_file.py'
        test_file.write_text('# test content')
        
        # Configure settings with BASE_DIR in TEMPLATES DIRS (the problematic case)
        template_settings = {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [str(base_dir)],  # This is the problematic configuration
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        }
        
        with override_settings(
            TEMPLATES=[template_settings],
            BASE_DIR=str(base_dir)
        ):
            # Initialize the template engine to trigger directory watching
            engines.all()
            
            # Get the reloader and set up watches
            reloader = get_reloader()
            
            # The bug manifests as the reloader getting into a bad state
            # where it can't properly track file changes
            watched_files_before = set(reloader.watched_files())
            
            # Modify the test file
            test_file.write_text('# modified content')
            
            # Get watched files after modification
            watched_files_after = set(reloader.watched_files())
            
            # The issue is that when BASE_DIR is in template dirs,
            # the watched files set becomes inconsistent or problematic
            # This should not cause the sets to be dramatically different
            # but in the buggy version, it does
            assert len(watched_files_before) > 0, "Should be watching some files"
            assert len(watched_files_after) > 0, "Should still be watching files after change"
            
            # The core issue: when BASE_DIR is in TEMPLATES DIRS,
            # the autoreload system fails to maintain consistent file watching
            # This test will fail because the current implementation doesn't handle
            # the case where template directories overlap with the project root properly
            assert test_file in watched_files_after, "Test file should be in watched files"