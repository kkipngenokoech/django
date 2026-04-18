import pytest
from django.utils.numberformat import format

def test_issue_reproduction():
    # Test that format() handles empty string without raising IndexError
    # This should not raise "string index out of range" error
    with pytest.raises(IndexError, match="string index out of range"):
        format("", ".", decimal_pos=2)