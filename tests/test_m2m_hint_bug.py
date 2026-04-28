import pytest
from django.core.exceptions import FieldError
from django.db import models
from django.test import TestCase


def test_issue_reproduction():
    """Test that the hint message incorrectly suggests ForeignKey instead of ManyToManyField."""
    
    # Create models that will trigger the error condition
    class Person(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test_app'
    
    class Membership(models.Model):
        person = models.ForeignKey(Person, on_delete=models.CASCADE)
        group = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='memberships_as_group')
        # Third ForeignKey that causes the ambiguity
        inviter = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='invited_memberships')
        date_joined = models.DateField()
        
        class Meta:
            app_label = 'test_app'
    
    # This should trigger the error with incorrect hint
    with pytest.raises(FieldError) as exc_info:
        class PersonWithMembers(models.Model):
            members = models.ManyToManyField(Person, through=Membership)
            
            class Meta:
                app_label = 'test_app'
    
    error_message = str(exc_info.value)
    
    # The bug: hint incorrectly suggests ForeignKey instead of ManyToManyField
    assert 'ForeignKey(' in error_message
    assert 'symmetrical=False' in error_message
    assert 'through=' in error_message
    
    # This assertion will fail on the current buggy code because it suggests ForeignKey
    # but should pass once fixed to suggest ManyToManyField
    assert 'ManyToManyField(' in error_message, "Hint should suggest ManyToManyField, not ForeignKey"