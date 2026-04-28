import os
import tempfile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import MemoryUploadedFile, TemporaryUploadedFile
from django.test import override_settings


def test_issue_reproduction():
    """Test that file permissions are inconsistent when FILE_UPLOAD_PERMISSIONS is None."""
    # Ensure FILE_UPLOAD_PERMISSIONS is None (default)
    with override_settings(FILE_UPLOAD_PERMISSIONS=None):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileSystemStorage(location=temp_dir)
            
            # Create a MemoryUploadedFile (small file, stays in memory)
            memory_content = b"small content"
            memory_file = MemoryUploadedFile(
                name="memory_test.txt",
                content_type="text/plain",
                size=len(memory_content),
                charset="utf-8"
            )
            memory_file.write(memory_content)
            memory_file.seek(0)
            
            # Create a TemporaryUploadedFile (simulates large file)
            temp_file = TemporaryUploadedFile(
                name="temp_test.txt",
                content_type="text/plain",
                size=0,
                charset="utf-8"
            )
            temp_file.write(b"large content that goes to temp file")
            temp_file.seek(0)
            
            # Save both files
            memory_name = storage.save("memory_test.txt", memory_file)
            temp_name = storage.save("temp_test.txt", temp_file)
            
            # Get file permissions
            memory_path = storage.path(memory_name)
            temp_path = storage.path(temp_name)
            
            memory_perms = oct(os.stat(memory_path).st_mode)[-3:]
            temp_perms = oct(os.stat(temp_path).st_mode)[-3:]
            
            # The permissions should be the same, but they're not!
            # MemoryUploadedFile gets created with 0o666 (minus umask)
            # TemporaryUploadedFile keeps the 0o600 from tempfile
            assert memory_perms == temp_perms, f"Inconsistent permissions: memory={memory_perms}, temp={temp_perms}"