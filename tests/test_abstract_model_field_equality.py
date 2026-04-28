import pytest
from django.db import models
from django.test import TestCase


def test_issue_reproduction():
    """Test that fields from abstract models should not be equal across different concrete models."""
    
    class AbstractModel(models.Model):
        class Meta:
            abstract = True
        myfield = models.IntegerField()
    
    class ConcreteModelB(AbstractModel):
        pass
    
    class ConcreteModelC(AbstractModel):
        pass
    
    # Get the fields from both concrete models
    field_b = ConcreteModelB._meta.get_field('myfield')
    field_c = ConcreteModelC._meta.get_field('myfield')
    
    # These fields should NOT be equal since they belong to different models
    assert field_b != field_c, "Fields from different concrete models should not be equal"
    
    # When put in a set, both fields should be preserved (no deduplication)
    field_set = {field_b, field_c}
    assert len(field_set) == 2, "Set should contain both fields, not deduplicate them"