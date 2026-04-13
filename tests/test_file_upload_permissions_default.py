import pytest
from django.conf import global_settings

def test_issue_reproduction():
    """Test that FILE_UPLOAD_PERMISSIONS has a default value of 0o644."""
    # This test fails on the current code where FILE_UPLOAD_PERMISSIONS is None
    # and will pass once it's set to 0o644 by default
    assert global_settings.FILE_UPLOAD_PERMISSIONS == 0o644, (
        f"Expected FILE_UPLOAD_PERMISSIONS to be 0o644, but got {global_settings.FILE_UPLOAD_PERMISSIONS}"
    )