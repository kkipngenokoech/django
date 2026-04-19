import pytest
from django.db import models
from django.core.checks import Error
from django.test import TestCase


def test_issue_reproduction():
    """Test that the hint for recursive relationship error uses correct field type."""
    
    class Person(models.Model):
        name = models.CharField(max_length=100)
        friends = models.ManyToManyField('self', through='Friendship')
        
        class Meta:
            app_label = 'test_app'
    
    class Friendship(models.Model):
        from_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='from_friendships')
        to_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='to_friendships')
        # Adding a third ForeignKey to trigger the error
        witness = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='witnessed_friendships')
        date_created = models.DateTimeField(auto_now_add=True)
        
        class Meta:
            app_label = 'test_app'
    
    # Get the ManyToManyField and run its checks
    friends_field = Person._meta.get_field('friends')
    errors = friends_field.check()
    
    # Should find an error about ambiguous through fields
    assert len(errors) > 0
    
    # Find the error with the incorrect hint
    hint_error = None
    for error in errors:
        if hasattr(error, 'hint') and error.hint and 'ForeignKey' in error.hint:
            hint_error = error
            break
    
    assert hint_error is not None, "Expected to find error with ForeignKey hint"
    
    # The bug: hint incorrectly suggests ForeignKey instead of ManyToManyField
    # and includes outdated 'symmetrical=False'
    assert 'ForeignKey' in hint_error.hint, "Hint should incorrectly mention ForeignKey (this is the bug)"
    assert 'symmetrical=False' in hint_error.hint, "Hint should incorrectly mention symmetrical=False (this is the bug)"