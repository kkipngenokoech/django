#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        USE_TZ=True,
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
        ],
    )

django.setup()

from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

def test_newline_issue():
    """Test that username validators reject usernames with trailing newlines."""
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # These usernames with trailing newlines should be rejected but currently pass
    username_with_newline = "validuser\n"
    
    print("Testing username with trailing newline:", repr(username_with_newline))
    
    # Test ASCII validator
    try:
        ascii_validator(username_with_newline)
        print("ASCII validator: PASSED (should have failed!)")
    except ValidationError:
        print("ASCII validator: FAILED (correctly rejected)")
    
    # Test Unicode validator
    try:
        unicode_validator(username_with_newline)
        print("Unicode validator: PASSED (should have failed!)")
    except ValidationError:
        print("Unicode validator: FAILED (correctly rejected)")

if __name__ == "__main__":
    test_newline_issue()