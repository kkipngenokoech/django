from django.utils import text

def test_issue_reproduction():
    # Test the specific case mentioned in the issue
    result = text.slugify("___This is a test ---")
    expected = "this-is-a-test"
    assert result == expected, f"Expected '{expected}', but got '{result}'"
    
    # Test additional edge cases that should also be fixed
    assert text.slugify("---hello world___") == "hello-world"
    assert text.slugify("_-_test_-_") == "test"
    assert text.slugify("---") == ""
    assert text.slugify("___") == ""