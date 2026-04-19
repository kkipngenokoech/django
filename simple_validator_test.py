#!/usr/bin/env python
"""
Simple test to verify the username validators work correctly.
This avoids Django setup issues by testing the regex directly.
"""
import sys
import os

# Add the django directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Import the validators directly
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator

def test_validators():
    """Test that the validators correctly reject usernames with trailing newlines."""
    
    # Create validator instances
    ascii_validator = ASCIIUsernameValidator()
    unicode_validator = UnicodeUsernameValidator()
    
    # Test cases
    test_cases = [
        ("validuser", True, "Valid username should pass"),
        ("validuser\n", False, "Username with trailing newline should fail"),
        ("valid.user", True, "Username with dot should pass"),
        ("valid@user.com", True, "Username with @ should pass"),
        ("valid+user", True, "Username with + should pass"),
        ("valid-user", True, "Username with - should pass"),
        ("user_name", True, "Username with underscore should pass"),
        ("invalid user", False, "Username with space should fail"),
        ("\nvaliduser", False, "Username with leading newline should fail"),
    ]
    
    print("Testing ASCIIUsernameValidator and UnicodeUsernameValidator")
    print("=" * 60)
    
    all_passed = True
    
    for username, should_pass, description in test_cases:
        # Test ASCII validator
        try:
            ascii_validator(username)
            ascii_passed = True
        except Exception:
            ascii_passed = False
        
        # Test Unicode validator
        try:
            unicode_validator(username)
            unicode_passed = True
        except Exception:
            unicode_passed = False
        
        # Check results
        ascii_correct = ascii_passed == should_pass
        unicode_correct = unicode_passed == should_pass
        
        status_ascii = "✓" if ascii_correct else "✗"
        status_unicode = "✓" if unicode_correct else "✗"
        
        print(f"{status_ascii} ASCII   | {status_unicode} Unicode | {repr(username):20} | {description}")
        
        if not (ascii_correct and unicode_correct):
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        return True
    else:
        print("✗ Some tests failed!")
        return False

if __name__ == "__main__":
    success = test_validators()
    sys.exit(0 if success else 1)