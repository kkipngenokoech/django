import pytest
from django.forms import DurationField
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that DurationField error message shows correct format string."""
    field = DurationField()
    
    # Try to trigger a validation error with invalid input
    with pytest.raises(ValidationError) as exc_info:
        field.clean('invalid_duration_format')
    
    # Check if the error message contains the incorrect format string
    error_message = str(exc_info.value)
    
    # The current (buggy) format string that should be corrected
    incorrect_format = '[DD] [HH:[MM:]]ss[.uuuuuu]'
    # The correct format string that should be used
    correct_format = '[DD] [[HH:]MM:]ss[.uuuuuu]'
    
    # This test will fail on the current code because it contains the incorrect format
    # and will pass once the format is corrected
    assert incorrect_format not in error_message, f"Error message still contains incorrect format: {error_message}"
    assert correct_format in error_message, f"Error message should contain correct format: {error_message}"