#!/usr/bin/env python
import re

def test_regex_behavior():
    """Test the current regex behavior with trailing newlines."""
    
    # Current regex pattern used by the validators
    current_pattern = r'^[\w.@+-]+$'
    
    # Fixed regex pattern that should be used
    fixed_pattern = r'\A[\w.@+-]+\Z'
    
    test_strings = [
        "validuser",      # Should match both
        "validuser\n",    # Should only match current (buggy), not fixed
        "valid.user",     # Should match both
        "valid@user.com", # Should match both
        "valid+user",     # Should match both
        "valid-user",     # Should match both
        "invalid user",   # Should match neither (space not allowed)
        "\nvaliduser",    # Should match neither (leading newline)
    ]
    
    print("Testing regex patterns:")
    print("Current pattern:", repr(current_pattern))
    print("Fixed pattern:  ", repr(fixed_pattern))
    print()
    
    current_regex = re.compile(current_pattern)
    fixed_regex = re.compile(fixed_pattern)
    
    for test_str in test_strings:
        current_match = bool(current_regex.match(test_str))
        fixed_match = bool(fixed_regex.match(test_str))
        
        print(f"String: {repr(test_str):20} | Current: {current_match:5} | Fixed: {fixed_match:5}")
        
        # The key test case: "validuser\n" should be rejected by the fixed pattern
        if test_str == "validuser\n":
            if current_match and not fixed_match:
                print("  ✓ This demonstrates the bug - current accepts, fixed rejects")
            else:
                print("  ✗ Unexpected behavior")

if __name__ == "__main__":
    test_regex_behavior()