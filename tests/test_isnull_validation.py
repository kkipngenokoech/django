import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase


class TestModel(models.Model):
    name = models.CharField(max_length=100, null=True)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that __isnull lookup should only accept boolean values."""
    # These should raise an error but currently don't
    with pytest.raises((ValueError, TypeError)):
        TestModel.objects.filter(name__isnull=1)  # truthy non-boolean
    
    with pytest.raises((ValueError, TypeError)):
        TestModel.objects.filter(name__isnull=0)  # falsey non-boolean
    
    with pytest.raises((ValueError, TypeError)):
        TestModel.objects.filter(name__isnull="true")  # string
    
    with pytest.raises((ValueError, TypeError)):
        TestModel.objects.filter(name__isnull=[])  # empty list
    
    # These should work fine (boolean values)
    TestModel.objects.filter(name__isnull=True)
    TestModel.objects.filter(name__isnull=False)