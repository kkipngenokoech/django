import pytest
from django.db import models
from django.test import TestCase
from django.core.exceptions import ValidationError


class TestModel(models.Model):
    name = models.CharField(max_length=100, null=True)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that __isnull lookup should only accept boolean values."""
    # This should work (boolean values)
    TestModel.objects.filter(name__isnull=True)
    TestModel.objects.filter(name__isnull=False)
    
    # These should raise an error but currently don't (non-boolean values)
    with pytest.raises((ValueError, TypeError)):
        TestModel.objects.filter(name__isnull=1)  # truthy integer
    
    with pytest.raises((ValueError, TypeError)):
        TestModel.objects.filter(name__isnull=0)  # falsey integer
        
    with pytest.raises((ValueError, TypeError)):
        TestModel.objects.filter(name__isnull="true")  # string
        
    with pytest.raises((ValueError, TypeError)):
        TestModel.objects.filter(name__isnull=[])  # empty list (falsey)