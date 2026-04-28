import pytest
from django.utils.numberformat import format


def test_empty_string_handling():
    """Test that formatting an empty string doesn't cause IndexError."""
    result = format("", ".", decimal_pos=2)
    assert result == "00"


def test_none_value_handling():
    """Test that formatting None doesn't cause IndexError."""
    result = format(None, ".", decimal_pos=2)
    assert result == "None00"


def test_whitespace_string_handling():
    """Test that formatting whitespace-only strings works correctly."""
    result = format(" ", ".", decimal_pos=2)
    assert result == " 00"


def test_normal_negative_number():
    """Test that normal negative numbers still work correctly."""
    result = format("-123.45", ".", decimal_pos=2)
    assert result == "-123.45"


def test_normal_positive_number():
    """Test that normal positive numbers still work correctly."""
    result = format("123.45", ".", decimal_pos=2)
    assert result == "123.45"


def test_issue_reproduction():
    """Test that formatting an empty string (representing null) doesn't cause IndexError."""
    # This should raise IndexError: string index out of range on the buggy code
    # when it tries to access str_number[0] on an empty string
    result = format("", ".", decimal_pos=2)
    # The function should handle empty strings gracefully instead of crashing
    assert result is not None
