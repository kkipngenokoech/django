import pytest
from django.http import HttpResponse


def test_issue_reproduction():
    """Test that HttpResponse properly handles memoryview objects."""
    # Test data
    original_bytes = b"My Content"
    memory_view = memoryview(original_bytes)
    
    # Create HttpResponse with memoryview
    response = HttpResponse(memory_view)
    
    # The bug: memoryview gets converted to string representation
    # instead of the actual bytes content
    # Current buggy behavior returns something like b'<memory at 0x...>'
    # Expected correct behavior should return b'My Content'
    assert response.content == original_bytes, f"Expected {original_bytes!r}, got {response.content!r}"
    
    # Test with different content to ensure it's not just coincidence
    test_data = b"Test binary data \x00\x01\x02\xff"
    test_memoryview = memoryview(test_data)
    response2 = HttpResponse(test_memoryview)
    assert response2.content == test_data, f"Expected {test_data!r}, got {response2.content!r}"
    
    # Test that regular bytes and strings still work (regression test)
    response_bytes = HttpResponse(b"Bytes content")
    assert response_bytes.content == b"Bytes content"
    
    response_str = HttpResponse("String content")
    assert response_str.content == b"String content"