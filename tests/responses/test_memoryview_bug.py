import pytest
from django.http import HttpResponse

def test_issue_reproduction():
    # Test that HttpResponse properly handles memoryview objects
    original_bytes = b'My Content'
    memory_view = memoryview(original_bytes)
    
    response = HttpResponse(memory_view)
    
    # This should be the original bytes, not a string representation of the memoryview
    assert response.content == original_bytes, f"Expected {original_bytes!r}, got {response.content!r}"