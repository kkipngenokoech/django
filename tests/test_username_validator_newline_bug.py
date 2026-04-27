import pytest
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that username validators incorrectly allow trailing newlines."""
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # These usernames with trailing newlines should be rejected but currently pass
    username_with_newline = "validuser\n"
    
    # This should raise ValidationError but currently doesn't (bug)
    with pytest.raises(ValidationError):
        ascii_validator(username_with_newline)
    
    with pytest.raises(ValidationError):
        unicode_validator(username_with_newline)