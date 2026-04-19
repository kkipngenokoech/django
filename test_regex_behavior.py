import re

# Test the problematic regex patterns
ascii_pattern = r'^[\w.@+-]+$'
unicode_pattern = r'^[\w.@+-]+$'

# Test usernames with trailing newlines
test_username = "validuser\n"

print("Testing problematic regex patterns:")
print(f"Username to test: {repr(test_username)}")

# Test ASCII pattern
ascii_match = re.match(ascii_pattern, test_username, re.ASCII)
print(f"ASCII pattern '{ascii_pattern}' matches: {ascii_match is not None}")

# Test Unicode pattern  
unicode_match = re.match(unicode_pattern, test_username)
print(f"Unicode pattern '{unicode_pattern}' matches: {unicode_match is not None}")

print("\nTesting fixed regex patterns:")
# Test the fixed patterns
fixed_ascii_pattern = r'\A[\w.@+-]+\Z'
fixed_unicode_pattern = r'\A[\w.@+-]+\Z'

# Test ASCII pattern
fixed_ascii_match = re.match(fixed_ascii_pattern, test_username, re.ASCII)
print(f"Fixed ASCII pattern '{fixed_ascii_pattern}' matches: {fixed_ascii_match is not None}")

# Test Unicode pattern  
fixed_unicode_match = re.match(fixed_unicode_pattern, test_username)
print(f"Fixed Unicode pattern '{fixed_unicode_pattern}' matches: {fixed_unicode_match is not None}")

print("\nTesting valid usernames (should match in both cases):")
valid_username = "validuser"
print(f"Valid username to test: {repr(valid_username)}")

# Test original patterns with valid username
ascii_match_valid = re.match(ascii_pattern, valid_username, re.ASCII)
unicode_match_valid = re.match(unicode_pattern, valid_username)
print(f"Original ASCII pattern matches valid username: {ascii_match_valid is not None}")
print(f"Original Unicode pattern matches valid username: {unicode_match_valid is not None}")

# Test fixed patterns with valid username
fixed_ascii_match_valid = re.match(fixed_ascii_pattern, valid_username, re.ASCII)
fixed_unicode_match_valid = re.match(fixed_unicode_pattern, valid_username)
print(f"Fixed ASCII pattern matches valid username: {fixed_ascii_match_valid is not None}")
print(f"Fixed Unicode pattern matches valid username: {fixed_unicode_match_valid is not None}")