import pytest
from django.db import models
from django.core.exceptions import ValidationError
from django.forms import DurationField as FormDurationField


def test_issue_reproduction():
    """Test that DurationField error message shows correct format."""
    # Test with form field since that's where validation error messages are shown
    field = FormDurationField()
    
    # Try to validate an invalid duration to trigger the error message
    with pytest.raises(ValidationError) as exc_info:
        field.clean('invalid_duration')
    
    error_message = str(exc_info.value)
    
    # The current (buggy) format shows: [DD] [HH:[MM:]]ss[.uuuuuu]
    # The correct format should be: [DD] [[HH:]MM:]ss[.uuuuuu]
    # This test will fail because the current code has the wrong format
    assert '[DD] [[HH:]MM:]ss[.uuuuuu]' in error_message, f"Expected correct format in error message, got: {error_message}"