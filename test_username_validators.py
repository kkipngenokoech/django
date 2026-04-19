#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
        ],
        SECRET_KEY='test-secret-key',
    )

django.setup()

from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

def test_current_behavior():
    """Test current behavior with trailing newlines."""
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # Test valid username
    try:
        ascii_validator("validuser")
        print("✓ ASCII validator accepts 'validuser'")
    except ValidationError:
        print("✗ ASCII validator rejects 'validuser'")
    
    try:
        unicode_validator("validuser")
        print("✓ Unicode validator accepts 'validuser'")
    except ValidationError:
        print("✗ Unicode validator rejects 'validuser'")
    
    # Test username with trailing newline (this should fail but currently passes)
    username_with_newline = "validuser\n"
    
    try:
        ascii_validator(username_with_newline)
        print("✗ ASCII validator incorrectly accepts 'validuser\\n'")
    except ValidationError:
        print("✓ ASCII validator correctly rejects 'validuser\\n'")
    
    try:
        unicode_validator(username_with_newline)
        print("✗ Unicode validator incorrectly accepts 'validuser\\n'")
    except ValidationError:
        print("✓ Unicode validator correctly rejects 'validuser\\n'")

if __name__ == "__main__":
    test_current_behavior()