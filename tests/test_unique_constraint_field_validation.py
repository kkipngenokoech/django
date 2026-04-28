import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.test import TestCase


def test_issue_reproduction():
    """Test that UniqueConstraint should validate field existence like unique_together does."""
    
    # First, demonstrate that unique_together properly validates field existence
    class ModelWithUniqueTogetherBadFields(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test'
            unique_together = [('name', 'nonexistent_field')]
    
    # This should raise models.E012 error for nonexistent field
    errors = ModelWithUniqueTogetherBadFields.check()
    assert len(errors) > 0
    assert any(error.id == 'models.E012' for error in errors)
    
    # Now test UniqueConstraint with nonexistent fields - this should also fail but currently doesn't
    class ModelWithUniqueConstraintBadFields(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test'
            constraints = [
                UniqueConstraint(fields=['name', 'nonexistent_field'], name='test_unique')
            ]
    
    # This should also raise models.E012 error for nonexistent field, but currently doesn't
    errors = ModelWithUniqueConstraintBadFields.check()
    
    # The bug: UniqueConstraint doesn't validate field existence
    # This assertion will FAIL on the current buggy code because no E012 error is raised
    assert len(errors) > 0, "UniqueConstraint should validate field existence but doesn't"
    assert any(error.id == 'models.E012' for error in errors), "Expected models.E012 error for nonexistent field in UniqueConstraint"