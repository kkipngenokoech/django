import os
import tempfile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import MemoryUploadedFile, TemporaryUploadedFile
from django.test import TestCase, override_settings


def test_issue_reproduction():
    """Test that FILE_UPLOAD_PERMISSIONS defaults to 0o644 to ensure consistent file permissions."""
    # The issue is that FILE_UPLOAD_PERMISSIONS should default to 0o644, not None
    # When it's None, TemporaryUploadedFile creates files with 0o600 permissions
    # while MemoryUploadedFile doesn't have this restriction
    
    # Check that the default value is 0o644 (this will fail on current code where it's None)
    assert settings.FILE_UPLOAD_PERMISSIONS == 0o644, f"Expected FILE_UPLOAD_PERMISSIONS to default to 0o644, got {settings.FILE_UPLOAD_PERMISSIONS}"
    
    # Additional verification: ensure the setting exists and has the expected type
    assert hasattr(settings, 'FILE_UPLOAD_PERMISSIONS'), "FILE_UPLOAD_PERMISSIONS setting should exist"
    assert isinstance(settings.FILE_UPLOAD_PERMISSIONS, int), "FILE_UPLOAD_PERMISSIONS should be an integer (octal)"
    assert oct(settings.FILE_UPLOAD_PERMISSIONS) == '0o644', f"FILE_UPLOAD_PERMISSIONS should be 0o644, got {oct(settings.FILE_UPLOAD_PERMISSIONS)}"
