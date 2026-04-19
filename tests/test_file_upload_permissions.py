import os
import tempfile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
from django.test import TestCase, override_settings


def test_issue_reproduction():
    """Test that FILE_UPLOAD_PERMISSIONS defaults to None causing inconsistent permissions."""
    # Verify the current default is None (the bug)
    assert settings.FILE_UPLOAD_PERMISSIONS is None
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = FileSystemStorage(location=temp_dir)
        
        # Test with a small file (uses MemoryUploadedFile path)
        small_file = SimpleUploadedFile("small.txt", b"small content")
        small_path = storage.save("small.txt", small_file)
        small_full_path = os.path.join(temp_dir, small_path)
        
        # Test with a large file that would use TemporaryUploadedFile
        # Create a TemporaryUploadedFile directly to simulate the problematic case
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"large content" * 1000)
            tmp.flush()
            
            # This simulates what happens with TemporaryUploadedFile
            temp_file = TemporaryUploadedFile("large.txt", "text/plain", len(b"large content" * 1000), "utf-8")
            temp_file.file = tmp
            
            large_path = storage.save("large.txt", temp_file)
            large_full_path = os.path.join(temp_dir, large_path)
        
        # Get file permissions
        small_perms = oct(os.stat(small_full_path).st_mode)[-3:]
        large_perms = oct(os.stat(large_full_path).st_mode)[-3:]
        
        # The issue: permissions are inconsistent when FILE_UPLOAD_PERMISSIONS is None
        # This assertion should fail on the current buggy code because permissions differ
        # but will pass once FILE_UPLOAD_PERMISSIONS defaults to 0o644
        assert small_perms == large_perms == "644", f"Inconsistent permissions: small={small_perms}, large={large_perms}"