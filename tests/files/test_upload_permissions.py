import os
import tempfile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings


def test_issue_reproduction():
    """Test that FILE_UPLOAD_PERMISSIONS defaults to None causing inconsistent permissions."""
    # Verify that FILE_UPLOAD_PERMISSIONS is None by default
    assert settings.FILE_UPLOAD_PERMISSIONS is None
    
    # Create a temporary directory for file storage
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = FileSystemStorage(location=temp_dir)
        
        # Create a small file (will use MemoryUploadedFile)
        small_content = b'small file content'
        small_file = SimpleUploadedFile('small.txt', small_content)
        
        # Create a large file (will use TemporaryUploadedFile)
        # FILE_UPLOAD_MAX_MEMORY_SIZE is 2621440 bytes by default
        large_content = b'x' * (settings.FILE_UPLOAD_MAX_MEMORY_SIZE + 1)
        large_file = SimpleUploadedFile('large.txt', large_content)
        
        # Save both files
        small_path = storage.save('small.txt', small_file)
        large_path = storage.save('large.txt', large_file)
        
        # Get the actual file paths
        small_full_path = storage.path(small_path)
        large_full_path = storage.path(large_path)
        
        # Get file permissions
        small_perms = oct(os.stat(small_full_path).st_mode)[-3:]
        large_perms = oct(os.stat(large_full_path).st_mode)[-3:]
        
        # This assertion should fail because permissions are inconsistent
        # Small files typically get 644 permissions while large files get 600
        assert small_perms == large_perms, f"File permissions are inconsistent: small={small_perms}, large={large_perms}"