import pytest
from django.db import models
from django.test import TestCase


class SimpleModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    # Create a model instance
    instance = SimpleModel(name='test')
    instance.save()
    
    # Store the original PK
    original_pk = instance.pk
    assert original_pk is not None
    
    # Delete the instance
    instance.delete()
    
    # The PK should be None after deletion
    assert instance.pk is None, f"Expected PK to be None after deletion, but got {instance.pk}"