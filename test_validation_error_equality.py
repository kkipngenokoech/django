import pytest
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    # Test basic equality - identical ValidationErrors should be equal
    error1 = ValidationError('This field is required.')
    error2 = ValidationError('This field is required.')
    assert error1 == error2, "ValidationErrors with identical messages should be equal"
    
    # Test equality with code parameter
    error3 = ValidationError('Invalid value', code='invalid')
    error4 = ValidationError('Invalid value', code='invalid')
    assert error3 == error4, "ValidationErrors with identical messages and codes should be equal"
    
    # Test equality with params
    error5 = ValidationError('Value %(value)s is invalid', params={'value': 'test'})
    error6 = ValidationError('Value %(value)s is invalid', params={'value': 'test'})
    assert error5 == error6, "ValidationErrors with identical messages and params should be equal"
    
    # Test inequality with different messages
    error7 = ValidationError('This field is required.')
    error8 = ValidationError('This field is invalid.')
    assert error7 != error8, "ValidationErrors with different messages should not be equal"
    
    # Test inequality with different codes
    error9 = ValidationError('Invalid value', code='invalid')
    error10 = ValidationError('Invalid value', code='required')
    assert error9 != error10, "ValidationErrors with different codes should not be equal"
    
    # Test equality with list of errors (order-independent)
    error11 = ValidationError(['Error 1', 'Error 2'])
    error12 = ValidationError(['Error 2', 'Error 1'])
    assert error11 == error12, "ValidationErrors with same errors in different order should be equal"
    
    # Test equality with dict of errors (order-independent)
    error13 = ValidationError({'field1': ['Error 1'], 'field2': ['Error 2']})
    error14 = ValidationError({'field2': ['Error 2'], 'field1': ['Error 1']})
    assert error13 == error14, "ValidationErrors with same field errors in different order should be equal"
    
    # Test nested ValidationErrors
    nested1 = ValidationError(ValidationError('Nested error'))
    nested2 = ValidationError(ValidationError('Nested error'))
    assert nested1 == nested2, "Nested ValidationErrors with identical content should be equal"
    
    # Test hash consistency (ValidationErrors should be hashable if they're equal)
    error15 = ValidationError('Test error')
    error16 = ValidationError('Test error')
    if error15 == error16:
        assert hash(error15) == hash(error16), "Equal ValidationErrors should have equal hashes"