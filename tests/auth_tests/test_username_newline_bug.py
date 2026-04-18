import pytest
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that username validators reject usernames with trailing newlines."""
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # These usernames have trailing newlines and should be rejected
    invalid_usernames = [
        "validuser\n",
        "test123\n",
        "user.name\n",
        "user@domain\n",
        "user+tag\n",
        "user-name\n"
    ]
    
    for username in invalid_usernames:
        # Both validators should reject usernames with trailing newlines
        with pytest.raises(ValidationError):
            ascii_validator(username)
        
        with pytest.raises(ValidationError):
            unicode_validator(username)