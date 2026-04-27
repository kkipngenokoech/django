#!/usr/bin/env python
"""
Simple test to verify the username validator fix works correctly.
This test directly imports the validators and tests them without Django setup.
"""
import sys
import os

# Add the django directory to the path so we can import the validators
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Import the validators directly
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.core.exceptions import ValidationError

def test_validators():
    """Test that both validators correctly reject usernames with newlines."""
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # Test cases
    valid_usernames = [
        'validuser',
        'user.name',
        'user@domain',
        'user+tag',
        'user-name',
        'user_name',
    ]
    
    invalid_usernames_with_newlines = [
        'validuser\n',  # trailing newline
        '\nvaliduser',  # leading newline  
        'valid\nuser',  # newline in middle
    ]
    
    print("Testing valid usernames (should pass):")
    for username in valid_usernames:
        try:
            ascii_validator(username)
            unicode_validator(username)
            print(f"  ✓ {repr(username)} - PASSED")
        except ValidationError as e:
            print(f"  ✗ {repr(username)} - FAILED: {e}")
            return False
    
    print("\nTesting invalid usernames with newlines (should fail):")
    for username in invalid_usernames_with_newlines:
        ascii_failed = False
        unicode_failed = False
        
        try:
            ascii_validator(username)
        except ValidationError:
            ascii_failed = True
            
        try:
            unicode_validator(username)
        except ValidationError:
            unicode_failed = True
            
        if ascii_failed and unicode_failed:
            print(f"  ✓ {repr(username)} - CORRECTLY REJECTED")
        else:
            print(f"  ✗ {repr(username)} - INCORRECTLY ACCEPTED (ASCII: {not ascii_failed}, Unicode: {not unicode_failed})")
            return False
    
    print("\n✓ All tests passed! The fix is working correctly.")
    return True

if __name__ == "__main__":
    success = test_validators()
    sys.exit(0 if success else 1)