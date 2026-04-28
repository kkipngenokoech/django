import pytest
from django.utils.text import slugify

def test_issue_reproduction():
    """Test that slugify strips leading and trailing dashes and underscores."""
    # Test the exact example from the issue
    result = slugify("___This is a test ---")
    expected = "this-is-a-test"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    # Test additional edge cases with leading/trailing dashes and underscores
    assert slugify("---hello world___") == "hello-world"
    assert slugify("_-_test_-_") == "test"
    assert slugify("___") == ""
    assert slugify("---") == ""
    assert slugify("_-_-_") == ""
    assert slugify("__hello__") == "hello"
    assert slugify("--world--") == "world"
    
    # Test mixed leading/trailing characters
    assert slugify("_-hello world-_") == "hello-world"
    assert slugify("--__test__--") == "test"
    
    # Test that internal dashes/underscores are preserved
    assert slugify("hello_world-test") == "hello_world-test"
    
    # Test normal cases still work
    assert slugify("Hello World") == "hello-world"
    assert slugify("test") == "test"