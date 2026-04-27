import pytest
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    """Test that username validators reject usernames ending with newlines."""
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # Test usernames that should be valid (no newlines)
    valid_usernames = ['testuser', 'test.user', 'test@example.com', 'test+user', 'test-user', 'test_user']
    
    for username in valid_usernames:
        # These should not raise ValidationError
        ascii_validator(username)
        unicode_validator(username)
    
    # Test usernames with trailing newlines - these should be REJECTED but currently pass
    invalid_usernames_with_newlines = [
        'testuser\n',
        'test.user\n', 
        'test@example.com\n',
        'test+user\n',
        'test-user\n',
        'test_user\n'
    ]
    
    for username in invalid_usernames_with_newlines:
        # These should raise ValidationError but currently don't due to the $ regex issue
        with pytest.raises(ValidationError):
            ascii_validator(username)
        
        with pytest.raises(ValidationError):
            unicode_validator(username)