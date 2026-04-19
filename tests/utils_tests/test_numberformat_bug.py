import pytest
from django.utils.numberformat import format

def test_issue_reproduction():
    """Test that format() handles empty string without IndexError."""
    # This should raise IndexError: string index out of range on buggy code
    # when str_number[0] is accessed on an empty string
    with pytest.raises(IndexError, match="string index out of range"):
        format("", ".", decimal_pos=2)