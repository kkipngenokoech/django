import pytest
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    # Test that ValidationErrors with identical messages should be equal
    error1 = ValidationError('This field is required.')
    error2 = ValidationError('This field is required.')
    
    # This should pass but currently fails because ValidationError has no __eq__ method
    assert error1 == error2
    
    # Test with list of errors (order-independent)
    error3 = ValidationError(['Error A', 'Error B'])
    error4 = ValidationError(['Error B', 'Error A'])
    
    # This should pass but currently fails
    assert error3 == error4
    
    # Test with error dictionaries
    error5 = ValidationError({'field1': ['Error 1'], 'field2': ['Error 2']})
    error6 = ValidationError({'field2': ['Error 2'], 'field1': ['Error 1']})
    
    # This should pass but currently fails
    assert error5 == error6