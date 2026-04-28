import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.test import TestCase


def test_issue_reproduction():
    """Test that UniqueConstraint should validate field existence like unique_together does."""
    
    # First, demonstrate that unique_together properly validates field existence
    class ModelWithUniqueTogetherBadField(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test'
            unique_together = [('name', 'nonexistent_field')]
    
    # This should raise validation errors for unique_together
    errors = ModelWithUniqueTogetherBadField.check()
    unique_together_errors = [e for e in errors if e.id == 'models.E012']
    assert len(unique_together_errors) > 0, "unique_together should raise E012 for nonexistent fields"
    
    # Now test UniqueConstraint with nonexistent field - this should also fail but currently doesn't
    class ModelWithUniqueConstraintBadField(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test'
            constraints = [
                UniqueConstraint(fields=['name', 'nonexistent_field'], name='test_unique')
            ]
    
    # This should raise validation errors for UniqueConstraint but currently doesn't
    errors = ModelWithUniqueConstraintBadField.check()
    constraint_errors = [e for e in errors if 'nonexistent_field' in str(e.msg)]
    
    # This assertion will FAIL on the current code because UniqueConstraint doesn't validate fields
    assert len(constraint_errors) > 0, "UniqueConstraint should validate field existence like unique_together does"