import pytest
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that username validators reject usernames with trailing newlines."""
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # These usernames with trailing newlines should be rejected but currently pass
    invalid_usernames = [
        'user\n',
        'test@example.com\n',
        'user.name\n',
        'user+tag\n',
        'user-name\n'
    ]
    
    for username in invalid_usernames:
        # Both validators should raise ValidationError for usernames with trailing newlines
        with pytest.raises(ValidationError):
            ascii_validator(username)
        
        with pytest.raises(ValidationError):
            unicode_validator(username)