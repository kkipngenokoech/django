import pytest
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    """Test that username validators reject usernames with trailing newlines."""
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # Test usernames with trailing newlines that should be rejected
    invalid_usernames = [
        'validuser\n',  # single trailing newline
        'test@example.com\n',  # email-like username with newline
        'user.name\n',  # username with dot and newline
        'user+tag\n',  # username with plus and newline
        'user-name\n',  # username with dash and newline
        'user_name\n',  # username with underscore and newline
    ]
    
    # Test that ASCIIUsernameValidator rejects usernames with trailing newlines
    for username in invalid_usernames:
        with pytest.raises(ValidationError, match=r'Enter a valid username'):
            ascii_validator(username)
    
    # Test that UnicodeUsernameValidator rejects usernames with trailing newlines
    for username in invalid_usernames:
        with pytest.raises(ValidationError, match=r'Enter a valid username'):
            unicode_validator(username)
    
    # Verify that valid usernames (without newlines) are still accepted
    valid_usernames = [
        'validuser',
        'test@example.com',
        'user.name',
        'user+tag',
        'user-name',
        'user_name',
    ]
    
    # These should not raise any exceptions
    for username in valid_usernames:
        ascii_validator(username)  # Should pass without exception
        unicode_validator(username)  # Should pass without exception