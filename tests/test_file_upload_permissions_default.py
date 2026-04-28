import pytest
from django.conf import global_settings

def test_issue_reproduction():
    """Test that FILE_UPLOAD_PERMISSIONS has a default value of 0o644."""
    # This test will fail on the current code because FILE_UPLOAD_PERMISSIONS is None
    # but should pass once the fix sets it to 0o644
    assert hasattr(global_settings, 'FILE_UPLOAD_PERMISSIONS')
    assert global_settings.FILE_UPLOAD_PERMISSIONS == 0o644