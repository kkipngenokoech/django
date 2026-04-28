import pytest
from django.db import models
from django.test import TestCase


def test_issue_reproduction():
    """Test that fields from abstract models should not be equal across different concrete models."""
    
    # Define abstract model with a field
    class AbstractModel(models.Model):
        class Meta:
            abstract = True
        myfield = models.IntegerField()
    
    # Define two concrete models inheriting from the abstract model
    class ConcreteModelB(AbstractModel):
        class Meta:
            app_label = 'test_app'
    
    class ConcreteModelC(AbstractModel):
        class Meta:
            app_label = 'test_app'
    
    # Get the fields from both models
    field_b = ConcreteModelB._meta.get_field('myfield')
    field_c = ConcreteModelC._meta.get_field('myfield')
    
    # These fields should NOT be equal since they belong to different models
    assert field_b != field_c, "Fields from different concrete models should not be equal"
    
    # When put in a set, both fields should be preserved (length should be 2)
    field_set = {field_b, field_c}
    assert len(field_set) == 2, "Set should contain both fields, not deduplicate them"
    
    # Hash values should be different
    assert hash(field_b) != hash(field_c), "Fields from different models should have different hash values"
    
    # Test ordering behavior - fields should be ordered consistently
    # but fields from different models should not be considered equal in ordering
    fields_list = [field_b, field_c]
    sorted_fields = sorted(fields_list)
    # The sorted list should still contain both fields
    assert len(sorted_fields) == 2, "Sorted list should contain both fields"