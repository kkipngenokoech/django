import pytest
from django.utils.text import slugify


def test_issue_reproduction():
    """Test that slugify strips leading underscores and trailing dashes."""
    # Test the exact example from the issue
    result = slugify("___This is a test ---")
    expected = "this-is-a-test"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    # Test additional edge cases with leading/trailing characters
    assert slugify("___hello___") == "hello"
    assert slugify("---world---") == "world"
    assert slugify("_-_test_-_") == "test"
    assert slugify("__-__multiple__-__") == "multiple"
    
    # Test that normal cases still work
    assert slugify("hello world") == "hello-world"
    assert slugify("Test String") == "test-string"
    
    # Test edge case with only underscores and dashes
    assert slugify("___---___") == ""
    
    # Test mixed leading/trailing characters
    assert slugify("_-hello world-_") == "hello-world"