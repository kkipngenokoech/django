import pytest
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that username validators reject usernames with trailing newlines."""
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # These usernames with trailing newlines should be rejected but currently pass
    username_with_newline = "validuser\n"
    
    # Test ASCII validator - this should raise ValidationError but doesn't
    with pytest.raises(ValidationError):
        ascii_validator(username_with_newline)
    
    # Test Unicode validator - this should raise ValidationError but doesn't
    with pytest.raises(ValidationError):
        unicode_validator(username_with_newline)