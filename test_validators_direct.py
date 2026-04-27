#!/usr/bin/env python
"""
Direct test of the validator regex patterns without importing Django.
"""
import re

# Test the regex patterns directly
current_pattern = r'^[\w.@+-]+$'
fixed_pattern = r'\A[\w.@+-]+\Z'

def test_regex_patterns():
    """Test that the fixed pattern correctly rejects newlines."""
    
    test_cases = [
        ('validuser', True, True),      # Should pass both
        ('validuser\n', True, False),   # Should fail with fixed pattern
        ('user.name', True, True),      # Should pass both
        ('user@domain', True, True),    # Should pass both
        ('user+tag', True, True),       # Should pass both
        ('user-name', True, True),      # Should pass both
        ('user_name', True, True),      # Should pass both
        ('\nvaliduser', False, False),  # Should fail both
        ('valid\nuser', False, False),  # Should fail both
    ]
    
    print("Testing regex patterns:")
    print(f"Current pattern: {current_pattern}")
    print(f"Fixed pattern:   {fixed_pattern}")
    print()
    
    all_passed = True
    
    for username, expected_current, expected_fixed in test_cases:
        current_match = bool(re.match(current_pattern, username))
        fixed_match = bool(re.match(fixed_pattern, username))
        
        current_ok = current_match == expected_current
        fixed_ok = fixed_match == expected_fixed
        
        status = "✓" if (current_ok and fixed_ok) else "✗"
        print(f"{status} {repr(username):15} | Current: {current_match:5} (expected {expected_current:5}) | Fixed: {fixed_match:5} (expected {expected_fixed:5})")
        
        if not (current_ok and fixed_ok):
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All regex pattern tests passed!")
        print("The fix correctly rejects usernames with trailing newlines while preserving valid usernames.")
    else:
        print("✗ Some tests failed!")
        
    return all_passed

if __name__ == "__main__":
    import sys
    success = test_regex_patterns()
    sys.exit(0 if success else 1)