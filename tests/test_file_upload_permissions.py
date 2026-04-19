import os
import tempfile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import MemoryUploadedFile, TemporaryUploadedFile
from django.test import TestCase, override_settings


def test_issue_reproduction():
    """Test that FILE_UPLOAD_PERMISSIONS defaults to 0o644 for consistent file permissions."""
    # Verify the current default is None (the bug)
    assert settings.FILE_UPLOAD_PERMISSIONS is None
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = FileSystemStorage(location=temp_dir)
        
        # Create a MemoryUploadedFile (small file)
        memory_file = MemoryUploadedFile(
            name='memory_test.txt',
            content_type='text/plain',
            size=10,
            charset='utf-8'
        )
        memory_file.write(b'test data')
        memory_file.seek(0)
        
        # Create a TemporaryUploadedFile (simulates large file)
        temp_file = TemporaryUploadedFile(
            name='temp_test.txt',
            content_type='text/plain',
            size=10,
            charset='utf-8'
        )
        temp_file.write(b'test data')
        temp_file.seek(0)
        
        # Save both files using the storage
        memory_path = storage.save('memory_test.txt', memory_file)
        temp_path = storage.save('temp_test.txt', temp_file)
        
        # Get the actual file paths
        memory_full_path = storage.path(memory_path)
        temp_full_path = storage.path(temp_path)
        
        # Get file permissions
        memory_perms = oct(os.stat(memory_full_path).st_mode)[-3:]
        temp_perms = oct(os.stat(temp_full_path).st_mode)[-3:]
        
        # This test demonstrates the inconsistency - it should fail because
        # TemporaryUploadedFile creates files with 0o600 permissions while
        # MemoryUploadedFile may have different permissions
        # The fix should make FILE_UPLOAD_PERMISSIONS default to 0o644
        assert memory_perms == temp_perms, f"File permissions inconsistent: memory={memory_perms}, temp={temp_perms}"