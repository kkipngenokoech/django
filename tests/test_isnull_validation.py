import pytest
from django.db import models
from django.test import TestCase
from django.core.exceptions import ValidationError


class TestModel(models.Model):
    name = models.CharField(max_length=100, null=True)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that __isnull lookup raises error for non-boolean values."""
    # These should raise ValueError for non-boolean values
    with pytest.raises(ValueError):
        TestModel.objects.filter(name__isnull=1)  # truthy non-boolean
    
    with pytest.raises(ValueError):
        TestModel.objects.filter(name__isnull=0)  # falsey non-boolean
    
    with pytest.raises(ValueError):
        TestModel.objects.filter(name__isnull="true")  # string
    
    with pytest.raises(ValueError):
        TestModel.objects.filter(name__isnull=[])  # empty list (falsey)
    
    # These should work fine (boolean values)
    TestModel.objects.filter(name__isnull=True)  # should not raise
    TestModel.objects.filter(name__isnull=False)  # should not raise