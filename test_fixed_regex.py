#!/usr/bin/env python
import re

def test_fixed_validators():
    """Test the fixed regex patterns."""
    
    # The fixed regex pattern now used by the validators
    fixed_pattern = r'\A[\w.@+-]+\Z'
    
    test_strings = [
        ("validuser", True),      # Should match
        ("validuser\n", False),   # Should NOT match (this is the fix)
        ("valid.user", True),     # Should match
        ("valid@user.com", True), # Should match
        ("valid+user", True),     # Should match
        ("valid-user", True),     # Should match
        ("invalid user", False),  # Should NOT match (space not allowed)
        ("\nvaliduser", False),   # Should NOT match (leading newline)
        ("", False),              # Should NOT match (empty string)
        ("user_name", True),      # Should match (underscore allowed)
    ]
    
    print("Testing fixed regex pattern:", repr(fixed_pattern))
    print()
    
    fixed_regex = re.compile(fixed_pattern)
    
    all_passed = True
    for test_str, expected in test_strings:
        actual = bool(fixed_regex.match(test_str))
        status = "✓" if actual == expected else "✗"
        print(f"{status} String: {repr(test_str):20} | Expected: {expected:5} | Actual: {actual:5}")
        if actual != expected:
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    test_fixed_validators()