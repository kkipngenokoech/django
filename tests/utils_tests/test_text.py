from django.utils.text import slugify

def test_issue_reproduction():
    """Test that slugify strips leading and trailing dashes and underscores."""
    result = slugify("___This is a test ---")
    expected = "this-is-a-test"
    assert result == expected, f"Expected '{expected}', but got '{result}'"