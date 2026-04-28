import pytest
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    # Test that ValidationErrors with identical messages should be equal
    error1 = ValidationError('This field is required.')
    error2 = ValidationError('This field is required.')
    
    # This should pass but currently fails because ValidationError has no __eq__ method
    assert error1 == error2
    
    # Test with list of messages
    error3 = ValidationError(['Error 1', 'Error 2'])
    error4 = ValidationError(['Error 1', 'Error 2'])
    assert error3 == error4
    
    # Test with dict of messages
    error5 = ValidationError({'field1': ['Error A'], 'field2': ['Error B']})
    error6 = ValidationError({'field1': ['Error A'], 'field2': ['Error B']})
    assert error5 == error6