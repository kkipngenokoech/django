import os
import tempfile
import threading
import time
from unittest import mock

from django.core.cache.backends.filebased import FileBasedCache


def test_issue_reproduction():
    """Test that has_key is susceptible to race conditions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = FileBasedCache(temp_dir, {})
        
        # Set a cache entry
        cache.set('test_key', 'test_value', timeout=1)
        
        # Get the file path
        fname = cache._key_to_file('test_key')
        
        # Mock os.path.exists to return True, but then delete the file
        # before open() is called to simulate the race condition
        original_exists = os.path.exists
        original_open = open
        
        def mock_exists(path):
            if path == fname:
                # File exists when checked
                result = original_exists(path)
                if result:
                    # Simulate another thread deleting the file right after exists() check
                    try:
                        os.remove(path)
                    except FileNotFoundError:
                        pass
                return result
            return original_exists(path)
        
        with mock.patch('os.path.exists', side_effect=mock_exists):
            # This should raise FileNotFoundError due to the race condition
            cache.has_key('test_key')