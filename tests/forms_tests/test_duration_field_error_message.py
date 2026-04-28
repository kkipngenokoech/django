import pytest
from django.forms import DurationField
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    """Test that DurationField shows incorrect format in error message."""
    field = DurationField()
    
    # Try to clean an invalid duration format that should trigger the format error
    with pytest.raises(ValidationError) as exc_info:
        field.clean('invalid_duration_format')
    
    # The error message should contain the format string
    error_message = str(exc_info.value)
    
    # Check if the current (incorrect) format is present
    # According to the issue, it currently shows: [DD] [HH:[MM:]]ss[.uuuuuu]
    # But it should show: [DD] [[HH:]MM:]ss[.uuuuuu]
    assert '[DD] [HH:[MM:]]ss[.uuuuuu]' in error_message, f"Expected incorrect format string not found in: {error_message}"