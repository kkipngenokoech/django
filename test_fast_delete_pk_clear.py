import pytest
from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps


@isolate_apps('test_delete')
class TestModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_delete'


def test_issue_reproduction():
    """Test that delete() on instances of models without dependencies clears PKs."""
    # Create a test model instance
    instance = TestModel(name='test')
    instance.save()
    
    # Verify the instance has a PK before deletion
    original_pk = instance.pk
    assert original_pk is not None
    
    # Delete the instance - this should go through fast delete path
    # since TestModel has no dependencies
    instance.delete()
    
    # The PK should be set to None after deletion
    assert instance.pk is None, f"Expected PK to be None after delete(), but got {instance.pk}"