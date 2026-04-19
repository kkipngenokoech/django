import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from django.test import TestCase


class TestModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that ModelChoiceField includes invalid value in error message."""
    # Create a queryset with some test data
    queryset = TestModel.objects.none()  # Empty queryset
    
    # Create ModelChoiceField and ModelMultipleChoiceField for comparison
    choice_field = ModelChoiceField(queryset=queryset)
    multi_choice_field = ModelMultipleChoiceField(queryset=queryset)
    
    invalid_value = "invalid_pk_123"
    
    # Test ModelMultipleChoiceField (should include value in error)
    with pytest.raises(ValidationError) as exc_info_multi:
        multi_choice_field.to_python([invalid_value])
    
    multi_error_message = str(exc_info_multi.value)
    
    # Test ModelChoiceField (currently doesn't include value in error)
    with pytest.raises(ValidationError) as exc_info_single:
        choice_field.to_python(invalid_value)
    
    single_error_message = str(exc_info_single.value)
    
    # The bug: ModelChoiceField should include the invalid value like ModelMultipleChoiceField does
    # This assertion will fail on current code because ModelChoiceField doesn't include the value
    assert invalid_value in single_error_message, f"Expected '{invalid_value}' to be in error message: {single_error_message}"
    
    # Verify that ModelMultipleChoiceField does include the value (this should pass)
    assert invalid_value in multi_error_message, f"Expected '{invalid_value}' to be in error message: {multi_error_message}"