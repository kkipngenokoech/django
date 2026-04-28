import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.test import TestCase


def test_issue_reproduction():
    """Test that UniqueConstraint should validate field existence like unique_together does."""
    
    class TestModel(models.Model):
        existing_field = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test'
            constraints = [
                UniqueConstraint(fields=['nonexistent_field'], name='test_unique')
            ]
    
    # This should raise a validation error for nonexistent field, but currently doesn't
    errors = TestModel.check()
    
    # The test expects an error to be raised for the nonexistent field
    # but the current implementation doesn't validate field existence
    assert len(errors) > 0, "Expected validation error for nonexistent field in UniqueConstraint"
    
    # Check that the error is about the nonexistent field
    field_errors = [error for error in errors if 'nonexistent_field' in str(error)]
    assert len(field_errors) > 0, "Expected specific error about nonexistent_field"