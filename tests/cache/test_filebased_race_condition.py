import os
import tempfile
import threading
import time
from django.core.cache.backends.filebased import FileBasedCache


def test_issue_reproduction():
    """Test that has_key raises FileNotFoundError due to race condition."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = FileBasedCache(temp_dir, {})
        
        # Set a cache entry that will expire immediately
        cache.set('test_key', 'test_value', timeout=0.001)
        
        # Wait for it to expire
        time.sleep(0.002)
        
        # Get the file path
        fname = cache._key_to_file('test_key')
        
        # Monkey patch os.path.exists to simulate race condition
        original_exists = os.path.exists
        original_open = open
        
        def patched_exists(path):
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
        
        # Apply the patch
        os.path.exists = patched_exists
        
        try:
            # This should raise FileNotFoundError due to race condition
            cache.has_key('test_key')
        finally:
            # Restore original functions
            os.path.exists = original_exists