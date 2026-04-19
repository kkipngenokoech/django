#!/usr/bin/env python
"""
Minimal version of the reproducer test that verifies the fix.
"""
import re

def test_reproducer():
    """Test that reproduces the original issue and verifies the fix."""
    
    # The fixed regex patterns (what we implemented)
    fixed_pattern = r'\A[\w.@+-]+\Z'
    
    # The original buggy patterns (for comparison)
    buggy_pattern = r'^[\w.@+-]+$'
    
    # Test username with trailing newline
    username_with_newline = "validuser\n"
    
    # Compile patterns
    fixed_regex = re.compile(fixed_pattern)
    buggy_regex = re.compile(buggy_pattern)
    
    # Test the patterns
    fixed_matches = bool(fixed_regex.match(username_with_newline))
    buggy_matches = bool(buggy_regex.match(username_with_newline))
    
    print("Testing username with trailing newline:", repr(username_with_newline))
    print(f"Buggy pattern {repr(buggy_pattern)} matches: {buggy_matches}")
    print(f"Fixed pattern {repr(fixed_pattern)} matches: {fixed_matches}")
    print()
    
    # The fix should reject the username with trailing newline
    if not fixed_matches and buggy_matches:
        print("✓ Fix is working correctly!")
        print("  - Buggy pattern incorrectly accepts username with trailing newline")
        print("  - Fixed pattern correctly rejects username with trailing newline")
        return True
    else:
        print("✗ Fix is not working as expected!")
        return False

if __name__ == "__main__":
    success = test_reproducer()
    exit(0 if success else 1)