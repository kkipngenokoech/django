import pytest
from django.views.static import was_modified_since

def test_issue_reproduction():
    # Test that empty string for If-Modified-Since header is handled gracefully
    # This should not raise an exception and should return True (indicating modification)
    result = was_modified_since(header="", mtime=1000, size=100)
    assert result is True
    
    # Test whitespace-only string as well
    result = was_modified_since(header="   ", mtime=1000, size=100)
    assert result is True