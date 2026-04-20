import os
import tempfile
import unittest.mock
from django.core.cache.backends.filebased import FileBasedCache


def test_issue_reproduction():
    """Test that has_key is susceptible to race conditions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = FileBasedCache(temp_dir, {})
        
        # Set a cache entry
        cache.set('test_key', 'test_value')
        
        # Get the file path
        fname = cache._key_to_file('test_key')
        
        # Verify file exists
        assert os.path.exists(fname)
        
        # Mock os.path.exists to return True, but delete the file before open()
        original_exists = os.path.exists
        original_open = open
        
        def mock_exists(path):
            if path == fname:
                return True
            return original_exists(path)
        
        def mock_open(path, *args, **kwargs):
            if path == fname:
                # Delete the file right before opening to simulate race condition
                if os.path.exists(path):
                    os.remove(path)
            return original_open(path, *args, **kwargs)
        
        with unittest.mock.patch('os.path.exists', side_effect=mock_exists), \
             unittest.mock.patch('builtins.open', side_effect=mock_open):
            # This should raise FileNotFoundError due to race condition
            cache.has_key('test_key')