import pytest
from django.db.models import Q

def test_issue_reproduction():
    """Test that Q objects with non-pickleable values can be combined with | operator."""
    # This should not raise a TypeError
    q1 = Q()
    q2 = Q(x__in={}.keys())  # dict_keys is not pickleable
    
    # This should work without raising "TypeError: cannot pickle 'dict_keys' object"
    result = q1 | q2
    
    # Verify the result is a valid Q object
    assert isinstance(result, Q)
    assert str(result) == "(OR: ('x__in', dict_keys([])))"
    
    # Also test the reverse order
    result2 = q2 | q1
    assert isinstance(result2, Q)