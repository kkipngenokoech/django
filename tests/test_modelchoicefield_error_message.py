import pytest
from django.core.exceptions import ValidationError
from django.forms.models import ModelChoiceField
from django.test import TestCase
from django.contrib.auth.models import User


def test_issue_reproduction():
    """Test that ModelChoiceField does not include invalid value in error message."""
    # Create a ModelChoiceField with User queryset
    field = ModelChoiceField(queryset=User.objects.all())
    
    # Try to validate an invalid choice (non-existent user ID)
    invalid_value = 99999
    
    with pytest.raises(ValidationError) as exc_info:
        field.clean(invalid_value)
    
    # The error message should contain the invalid value, but it doesn't in the current implementation
    error_message = str(exc_info.value.message)
    
    # This assertion will fail because the current implementation doesn't include %(value)s
    # The error message will be "Select a valid choice. That choice is not one of the available choices."
    # instead of "Select a valid choice. 99999 is not one of the available choices."
    assert str(invalid_value) in error_message, f"Expected invalid value '{invalid_value}' to be in error message: '{error_message}'"