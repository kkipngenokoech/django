import pytest
from django.db import models
from django.db.models import Value, IntegerField
from django.db import NotSupportedError
from django.test import TestCase


class TestModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that distinct() on union queryset should raise NotSupportedError."""
    # Create querysets with annotations
    qs1 = TestModel.objects.filter(name='test1').annotate(rank=Value(0, IntegerField()))
    qs2 = TestModel.objects.filter(name='test2').annotate(rank=Value(1, IntegerField()))
    
    # Create union queryset
    union_qs = qs1.union(qs2)
    
    # This should raise NotSupportedError but currently doesn't
    with pytest.raises(NotSupportedError, match=r".*distinct.*union.*"):
        union_qs.distinct()