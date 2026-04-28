import pytest
from django.test import TestCase
from django.db import models
from django.forms import ModelMultipleChoiceField


class Publication(models.Model):
    name = models.CharField(max_length=100, default='test')
    
    class Meta:
        app_label = 'test_app'


class Article(models.Model):
    publications = models.ManyToManyField(to=Publication, blank=True)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that QuerySet.none() works properly on combined querysets."""
    # Test with OR query (| operator) - this should work correctly
    or_queryset = Publication.objects.filter(id__lt=2) | Publication.objects.filter(id__gt=5)
    or_none_queryset = or_queryset.none()
    
    # Test with union() - this is the broken case
    union_queryset = Publication.objects.filter(id__lt=2).union(
        Publication.objects.filter(id__gt=5)
    )
    union_none_queryset = union_queryset.none()
    
    # Both should return empty querysets
    assert list(or_none_queryset) == [], "OR queryset.none() should return empty list"
    assert list(union_none_queryset) == [], "Union queryset.none() should return empty list"
    
    # Test count() as well
    assert or_none_queryset.count() == 0, "OR queryset.none().count() should be 0"
    assert union_none_queryset.count() == 0, "Union queryset.none().count() should be 0"
    
    # Test exists() as well
    assert not or_none_queryset.exists(), "OR queryset.none().exists() should be False"
    assert not union_none_queryset.exists(), "Union queryset.none().exists() should be False"
    
    # Test with intersection and difference as well
    intersection_queryset = Publication.objects.filter(id__lt=10).intersection(
        Publication.objects.filter(id__gt=0)
    )
    intersection_none_queryset = intersection_queryset.none()
    assert list(intersection_none_queryset) == [], "Intersection queryset.none() should return empty list"
    
    difference_queryset = Publication.objects.filter(id__lt=10).difference(
        Publication.objects.filter(id__gt=5)
    )
    difference_none_queryset = difference_queryset.none()
    assert list(difference_none_queryset) == [], "Difference queryset.none() should return empty list"