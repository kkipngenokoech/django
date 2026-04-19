import pytest
from django.db import models
from django.test import TestCase


def test_issue_reproduction():
    """Test that fields from different models inheriting from abstract models are not equal."""
    
    class A(models.Model):
        class Meta:
            abstract = True
        myfield = models.IntegerField()
    
    class B(A):
        class Meta:
            app_label = 'test_app'
    
    class C(A):
        class Meta:
            app_label = 'test_app'
    
    # Get the fields from both models
    field_b = B._meta.get_field('myfield')
    field_c = C._meta.get_field('myfield')
    
    # These fields should NOT be equal since they belong to different models
    assert field_b != field_c, "Fields from different models should not be equal"
    
    # When put in a set, both fields should be preserved (length should be 2)
    field_set = {field_b, field_c}
    assert len(field_set) == 2, f"Expected 2 fields in set, got {len(field_set)}"
    
    # This is the current buggy behavior that should be fixed
    # Currently this assertion will fail because the fields are considered equal
    assert field_b == field_c  # This currently passes but shouldn't