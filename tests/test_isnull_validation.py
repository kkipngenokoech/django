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
    # These non-boolean values should raise ValueError but currently don't
    non_boolean_values = [1, 0, 'true', 'false', [], [1], {}, {'a': 1}]
    
    for value in non_boolean_values:
        with pytest.raises(ValueError, match=r".*boolean.*"):
            # This should raise ValueError but currently doesn't
            TestModel.objects.filter(name__isnull=value)
    
    # These boolean values should work fine
    TestModel.objects.filter(name__isnull=True)  # Should work
    TestModel.objects.filter(name__isnull=False)  # Should work