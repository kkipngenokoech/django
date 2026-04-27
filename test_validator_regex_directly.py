#!/usr/bin/env python
"""
Test the validator regex patterns directly without importing Django.
"""
import re

def test_validator_patterns():
    """Test the regex patterns used by the validators."""
    
    # Read the current patterns from the validators file
    with open('django/contrib/auth/validators.py', 'r') as f:
        content = f.read()
    
    # Extract the regex patterns
    import ast
    
    # Find the regex patterns in the file
    lines = content.split('\n')
    ascii_regex = None
    unicode_regex = None
    
    for line in lines:
        if 'regex = ' in line and ascii_regex is None:
            # This should be the ASCII validator regex
            ascii_regex = line.split('regex = ')[1].strip()
            ascii_regex = ast.literal_eval(ascii_regex)
        elif 'regex = ' in line and unicode_regex is None:
            # This should be the Unicode validator regex
            unicode_regex = line.split('regex = ')[1].strip()
            unicode_regex = ast.literal_eval(unicode_regex)
    
    print(f"ASCII validator regex: {repr(ascii_regex)}")
    print(f"Unicode validator regex: {repr(unicode_regex)}")
    print()
    
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
        ("", False, "Empty string should fail"),
    ]
    
    # Compile the regex patterns
    ascii_pattern = re.compile(ascii_regex, re.ASCII)
    unicode_pattern = re.compile(unicode_regex)
    
    print("Testing regex patterns:")
    print("=" * 70)
    
    all_passed = True
    
    for username, should_pass, description in test_cases:
        # Test ASCII pattern
        ascii_match = bool(ascii_pattern.match(username))
        unicode_match = bool(unicode_pattern.match(username))
        
        ascii_correct = ascii_match == should_pass
        unicode_correct = unicode_match == should_pass
        
        status_ascii = "✓" if ascii_correct else "✗"
        status_unicode = "✓" if unicode_correct else "✗"
        
        print(f"{status_ascii} ASCII   | {status_unicode} Unicode | {repr(username):20} | {description}")
        
        if not (ascii_correct and unicode_correct):
            all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("✓ All tests passed!")
        return True
    else:
        print("✗ Some tests failed!")
        return False

if __name__ == "__main__":
    success = test_validator_patterns()
    exit(0 if success else 1)