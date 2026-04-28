import pytest
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    # Test that ValidationErrors with identical messages should equal each other
    # but currently don't because __eq__ method is missing
    
    # Case 1: Simple string messages
    error1 = ValidationError("This field is required.")
    error2 = ValidationError("This field is required.")
    assert error1 == error2, "ValidationErrors with identical string messages should be equal"
    
    # Case 2: List of messages (order independent)
    error3 = ValidationError(["Error A", "Error B"])
    error4 = ValidationError(["Error B", "Error A"])
    assert error3 == error4, "ValidationErrors with same messages in different order should be equal"
    
    # Case 3: Dictionary of field errors (order independent)
    error5 = ValidationError({"field1": ["Error 1"], "field2": ["Error 2"]})
    error6 = ValidationError({"field2": ["Error 2"], "field1": ["Error 1"]})
    assert error5 == error6, "ValidationErrors with same field errors in different order should be equal"
    
    # Case 4: Different messages should not be equal
    error7 = ValidationError("Different message")
    error8 = ValidationError("Another message")
    assert error7 != error8, "ValidationErrors with different messages should not be equal"