import pytest
from django.test import TestCase
from django.db import models
from django.test.utils import override_settings


class SimpleModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'


@override_settings(USE_TZ=False)
class TestModelDeletion(TestCase):
    def test_issue_reproduction(self):
        # Create and save a model instance with no dependencies
        instance = SimpleModel(name='test')
        instance.save()
        
        # Verify it has a primary key
        original_pk = instance.pk
        assert original_pk is not None
        
        # Delete the instance
        instance.delete()
        
        # The primary key should be set to None after deletion
        # This assertion will FAIL on the current buggy code
        assert instance.pk is None, f"Expected pk to be None after deletion, but got {instance.pk}"