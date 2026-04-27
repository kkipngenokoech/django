#!/usr/bin/env python
import re

# Current regex patterns from the validators
current_pattern = r'^[\w.@+-]+$'
proposed_pattern = r'\A[\w.@+-]+\Z'

# Test usernames
test_cases = [
    "validuser",      # Should pass
    "validuser\n",    # Should fail with new pattern
    "user.name",      # Should pass
    "user@domain",    # Should pass
    "user+tag",       # Should pass
    "user-name",      # Should pass
    "user_name",      # Should pass
    "\nvaliduser",    # Should fail
    "valid\nuser",    # Should fail
]

print("Testing regex patterns:")
print("Current pattern:", current_pattern)
print("Proposed pattern:", proposed_pattern)
print()

for username in test_cases:
    current_match = bool(re.match(current_pattern, username))
    proposed_match = bool(re.match(proposed_pattern, username))
    
    print(f"Username: {repr(username):15} | Current: {current_match:5} | Proposed: {proposed_match:5}")
    
    if current_match != proposed_match:
        print(f"  -> DIFFERENCE: Current allows but proposed rejects")
    print()