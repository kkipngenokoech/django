from django.utils.text import slugify

def test_issue_reproduction():
    # Test the specific example from the issue
    result = slugify("___This is a test ---")
    expected = "this-is-a-test"
    assert result == expected, f"Expected '{expected}' but got '{result}'"
    
    # Additional test cases for edge cases
    assert slugify("---hello---") == "hello"
    assert slugify("___world___") == "world"
    assert slugify("--_test_--") == "test"
    assert slugify("_-_hello world_-_") == "hello-world"