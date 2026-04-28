import pytest
from django.utils.numberformat import format

def test_issue_reproduction():
    # Test that formatting an empty string (representing null) doesn't cause IndexError
    # This should raise IndexError: string index out of range on the buggy code
    # when it tries to access str_number[0] on an empty string
    result = format("", ".", decimal_pos=2)
    # The function should handle empty strings gracefully instead of crashing
    assert result is not None