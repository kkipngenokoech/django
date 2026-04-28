import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.models import ModelChoiceField
from django.test import TestCase


class TestModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that ModelChoiceField does not include invalid value in error message."""
    # Create a queryset with some test objects
    queryset = TestModel.objects.none()  # Empty queryset
    
    # Create a ModelChoiceField
    field = ModelChoiceField(queryset=queryset)
    
    # Try to validate an invalid choice
    invalid_value = "invalid_choice_123"
    
    with pytest.raises(ValidationError) as exc_info:
        field.to_python(invalid_value)
    
    error_message = str(exc_info.value)
    
    # The bug is that the invalid value is NOT included in the error message
    # This assertion will FAIL on the current buggy code because the value is missing
    assert invalid_value in error_message, f"Expected '{invalid_value}' to be in error message: {error_message}"
    
    # Also verify the error code is 'invalid_choice'
    assert exc_info.value.code == 'invalid_choice'