import pytest
from django.db import models
from django.test import TestCase


def test_issue_reproduction():
    """Test that fields from different models inheriting from same abstract model are not equal."""
    
    class AbstractModel(models.Model):
        class Meta:
            abstract = True
        myfield = models.IntegerField()
    
    class ModelB(AbstractModel):
        pass
    
    class ModelC(AbstractModel):
        pass
    
    # Get the fields from both models
    field_b = ModelB._meta.get_field('myfield')
    field_c = ModelC._meta.get_field('myfield')
    
    # These fields should NOT be equal since they belong to different models
    # But currently they are equal due to only comparing creation_counter
    assert field_b != field_c, "Fields from different models should not be equal"
    
    # When put in a set, both fields should be preserved (length should be 2)
    field_set = {field_b, field_c}
    assert len(field_set) == 2, f"Expected 2 fields in set, got {len(field_set)}"