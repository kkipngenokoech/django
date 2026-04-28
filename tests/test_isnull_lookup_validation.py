import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase
from django.db.models.lookups import IsNull
from django.db.models import F


class TestModel(models.Model):
    name = models.CharField(max_length=100, null=True)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that __isnull lookup should only accept boolean values."""
    
    # Test that non-boolean values should raise an error
    # These should all raise ValueError but currently don't
    
    # Test with string 'false' - this is truthy but semantically wrong
    with pytest.raises(ValueError, match=r".*isnull.*boolean.*"):
        lookup = IsNull(F('name'), 'false')
        
    # Test with string 'true' - this is truthy but semantically wrong  
    with pytest.raises(ValueError, match=r".*isnull.*boolean.*"):
        lookup = IsNull(F('name'), 'true')
        
    # Test with integer 1 - truthy but not boolean
    with pytest.raises(ValueError, match=r".*isnull.*boolean.*"):
        lookup = IsNull(F('name'), 1)
        
    # Test with integer 0 - falsy but not boolean
    with pytest.raises(ValueError, match=r".*isnull.*boolean.*"):
        lookup = IsNull(F('name'), 0)
        
    # Test with empty string - falsy but not boolean
    with pytest.raises(ValueError, match=r".*isnull.*boolean.*"):
        lookup = IsNull(F('name'), '')
        
    # Test with non-empty string - truthy but not boolean
    with pytest.raises(ValueError, match=r".*isnull.*boolean.*"):
        lookup = IsNull(F('name'), 'hello')
        
    # Test with list - truthy but not boolean
    with pytest.raises(ValueError, match=r".*isnull.*boolean.*"):
        lookup = IsNull(F('name'), [1, 2, 3])
        
    # Test with None - should this be allowed? Based on issue, probably not
    with pytest.raises(ValueError, match=r".*isnull.*boolean.*"):
        lookup = IsNull(F('name'), None)
    
    # These should work fine - actual boolean values
    lookup_true = IsNull(F('name'), True)
    assert lookup_true.rhs is True
    
    lookup_false = IsNull(F('name'), False) 
    assert lookup_false.rhs is False