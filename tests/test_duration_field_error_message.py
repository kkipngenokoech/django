import pytest
from django.forms import DurationField
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that DurationField error message shows correct format string."""
    field = DurationField()
    
    # Try to validate an invalid duration that will trigger the format error
    with pytest.raises(ValidationError) as exc_info:
        field.clean('invalid_duration')
    
    error_message = str(exc_info.value)
    
    # The error message should contain the correct format string
    # Current (buggy) format: '[DD] [HH:[MM:]]ss[.uuuuuu]'
    # Expected (correct) format: '[DD] [[HH:]MM:]ss[.uuuuuu]'
    expected_format = '[DD] [[HH:]MM:]ss[.uuuuuu]'
    
    assert expected_format in error_message, f"Error message should contain correct format '{expected_format}', but got: {error_message}"