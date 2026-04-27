import pytest
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that username validators reject usernames with trailing newlines."""
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # These usernames have trailing newlines and should be rejected
    username_with_newline = "validuser\n"
    
    # Both validators should raise ValidationError for usernames with trailing newlines
    with pytest.raises(ValidationError):
        ascii_validator(username_with_newline)
    
    with pytest.raises(ValidationError):
        unicode_validator(username_with_newline)