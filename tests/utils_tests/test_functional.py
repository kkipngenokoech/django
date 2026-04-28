import pytest
from django.utils.functional import SimpleLazyObject


def test_issue_reproduction():
    """Test that SimpleLazyObject doesn't implement __radd__ causing reverse addition to fail."""
    # Create a SimpleLazyObject that wraps a string
    lazy_str = SimpleLazyObject(lambda: "world")
    
    # This should work if __radd__ was implemented
    # The string "hello " should be able to add the lazy object via reverse addition
    with pytest.raises(TypeError):
        result = "hello " + lazy_str