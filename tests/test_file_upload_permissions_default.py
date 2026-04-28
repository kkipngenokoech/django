import pytest
from django.conf import global_settings

def test_issue_reproduction():
    # Test that FILE_UPLOAD_PERMISSIONS currently defaults to None
    # This causes inconsistent file permissions between MemoryUploadedFile 
    # and TemporaryUploadedFile handlers
    assert global_settings.FILE_UPLOAD_PERMISSIONS is None
    
    # The issue is that None means no explicit permissions are set,
    # leading to system-dependent behavior. The fix should set it to 0o644
    # This test will fail until FILE_UPLOAD_PERMISSIONS is set to 0o644
    assert global_settings.FILE_UPLOAD_PERMISSIONS == 0o644