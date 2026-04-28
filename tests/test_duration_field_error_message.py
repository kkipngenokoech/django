import pytest
from django.forms import DurationField
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that DurationField error message shows correct format string."""
    field = DurationField()
    
    # Try to trigger a validation error with invalid input
    with pytest.raises(ValidationError) as exc_info:
        field.clean('invalid_duration')
    
    # The error message should contain the correct format string
    error_message = str(exc_info.value)
    
    # Current (incorrect) format: [DD] [HH:[MM:]]ss[.uuuuuu]
    # Expected (correct) format: [DD] [[HH:]MM:]ss[.uuuuuu]
    # This test will fail because the current code has the wrong format
    assert '[DD] [[HH:]MM:]ss[.uuuuuu]' in error_message, f"Expected correct format string in error message, got: {error_message}"