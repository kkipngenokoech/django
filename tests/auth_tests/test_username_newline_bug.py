from django.contrib.auth import validators
from django.core.exceptions import ValidationError
import pytest

def test_issue_reproduction():
    """Test that username validators reject usernames with trailing newlines."""
    ascii_validator = validators.ASCIIUsernameValidator()
    unicode_validator = validators.UnicodeUsernameValidator()
    
    # These usernames have trailing newlines and should be rejected
    invalid_usernames = [
        'validuser\n',  # trailing newline
        'test@example.com\n',  # trailing newline with valid chars
        'user.name+test\n',  # trailing newline with dots, plus
    ]
    
    # Test ASCII validator rejects trailing newlines
    for username in invalid_usernames:
        with pytest.raises(ValidationError, match=r'Enter a valid username'):
            ascii_validator(username)
    
    # Test Unicode validator rejects trailing newlines  
    for username in invalid_usernames:
        with pytest.raises(ValidationError, match=r'Enter a valid username'):
            unicode_validator(username)