import pytest
from django.utils.functional import SimpleLazyObject


def test_issue_reproduction():
    """Test that SimpleLazyObject doesn't implement __radd__ method."""
    # Create a SimpleLazyObject that wraps a string
    lazy_str = SimpleLazyObject(lambda: "world")
    
    # This should work but will fail because __radd__ is not implemented
    # When Python tries "hello" + lazy_str, it first tries lazy_str.__add__("hello")
    # which doesn't exist, then tries "hello".__radd__(lazy_str) which also doesn't work
    # because lazy_str doesn't have __radd__ to handle the reverse operation
    with pytest.raises(TypeError):
        result = "hello" + lazy_str
    
    # For comparison, this should work (regular addition)
    result = lazy_str + "!"
    assert result == "world!"