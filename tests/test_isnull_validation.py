import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase
from django.db.models.lookups import IsNull


class TestModel(models.Model):
    name = models.CharField(max_length=100, null=True)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that __isnull lookup should only accept boolean values."""
    
    # These should work (boolean values)
    try:
        # Test with True
        lookup_true = IsNull(TestModel._meta.get_field('name'), True)
        assert lookup_true.rhs is True
        
        # Test with False  
        lookup_false = IsNull(TestModel._meta.get_field('name'), False)
        assert lookup_false.rhs is False
    except Exception as e:
        pytest.fail(f"Boolean values should be accepted: {e}")
    
    # These should raise errors (non-boolean values)
    non_boolean_values = [
        'true',      # string 'true'
        'false',     # string 'false' 
        1,           # integer 1 (truthy)
        0,           # integer 0 (falsy)
        'yes',       # string 'yes' (truthy)
        '',          # empty string (falsy)
        [],          # empty list (falsy)
        [1],         # non-empty list (truthy)
        None,        # None (falsy)
    ]
    
    for value in non_boolean_values:
        with pytest.raises((ValueError, TypeError), match=r".*isnull.*boolean.*"):
            IsNull(TestModel._meta.get_field('name'), value)