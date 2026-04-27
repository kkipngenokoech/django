import pytest
from django.http import HttpResponse

def test_issue_reproduction():
    """Test that HttpResponse properly handles memoryview objects."""
    original_bytes = b"My Content"
    mv = memoryview(original_bytes)
    
    # Create HttpResponse with memoryview
    response = HttpResponse(mv)
    
    # The content should be the original bytes, not the string representation of memoryview
    assert response.content == original_bytes, f"Expected {original_bytes!r}, got {response.content!r}"