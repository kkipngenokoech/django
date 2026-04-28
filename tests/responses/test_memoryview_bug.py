import pytest
from django.http import HttpResponse

def test_issue_reproduction():
    """Test that HttpResponse properly handles memoryview objects."""
    
    # Test with regular bytes - this should work correctly
    response_bytes = HttpResponse(b"My Content")
    assert response_bytes.content == b"My Content"
    
    # Test with string - this should work correctly
    response_str = HttpResponse("My Content")
    assert response_str.content == b"My Content"
    
    # Test with memoryview - this currently fails but should work
    original_bytes = b"My Content"
    memory_view = memoryview(original_bytes)
    response_memoryview = HttpResponse(memory_view)
    
    # This assertion will fail on the current buggy code
    # The current code returns something like b'<memory at 0x7fcc47ab2648>'
    # instead of the actual content b'My Content'
    assert response_memoryview.content == b"My Content"
    
    # Additional test with different content to ensure it's not just coincidence
    binary_data = b"\x00\x01\x02\x03\xff\xfe\xfd"
    memory_view_binary = memoryview(binary_data)
    response_binary = HttpResponse(memory_view_binary)
    assert response_binary.content == binary_data
    
    # Test that the memoryview content is properly converted, not just string representation
    # This ensures we're getting the actual bytes, not a string conversion
    assert b"<memory at" not in response_memoryview.content
    assert b"<memory at" not in response_binary.content