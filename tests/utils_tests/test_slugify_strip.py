from django.utils import text

def test_issue_reproduction():
    # Test the specific case mentioned in the issue
    result = text.slugify("___This is a test ---")
    # This should be 'this-is-a-test' but currently returns '___this-is-a-test-'
    assert result == 'this-is-a-test', f"Expected 'this-is-a-test', got '{result}'"
    
    # Additional test cases for edge cases
    assert text.slugify("---hello---") == 'hello'
    assert text.slugify("___world___") == 'world'
    assert text.slugify("_-_test_-_") == 'test'
    assert text.slugify("--__--") == ''