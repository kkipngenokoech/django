import pytest
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    """Test that ValidationError instances with identical content should be equal."""
    
    # Test basic equality with same message
    error1 = ValidationError('This field is required.')
    error2 = ValidationError('This field is required.')
    assert error1 == error2, "ValidationErrors with identical messages should be equal"
    
    # Test equality with same message, code, and params
    error3 = ValidationError('Value %(value)s is invalid.', code='invalid', params={'value': 'test'})
    error4 = ValidationError('Value %(value)s is invalid.', code='invalid', params={'value': 'test'})
    assert error3 == error4, "ValidationErrors with identical message, code, and params should be equal"
    
    # Test inequality with different messages
    error5 = ValidationError('This field is required.')
    error6 = ValidationError('This field is invalid.')
    assert error5 != error6, "ValidationErrors with different messages should not be equal"
    
    # Test inequality with same message but different codes
    error7 = ValidationError('Invalid value.', code='invalid')
    error8 = ValidationError('Invalid value.', code='required')
    assert error7 != error8, "ValidationErrors with same message but different codes should not be equal"
    
    # Test inequality with same message and code but different params
    error9 = ValidationError('Value %(value)s is invalid.', code='invalid', params={'value': 'test1'})
    error10 = ValidationError('Value %(value)s is invalid.', code='invalid', params={'value': 'test2'})
    assert error9 != error10, "ValidationErrors with same message and code but different params should not be equal"
    
    # Test order-independent equality for list-based ValidationErrors
    error_list1 = ValidationError(['Error A', 'Error B'])
    error_list2 = ValidationError(['Error B', 'Error A'])
    assert error_list1 == error_list2, "ValidationErrors with same errors in different order should be equal"
    
    # Test order-independent equality for dict-based ValidationErrors
    error_dict1 = ValidationError({'field1': ['Error A'], 'field2': ['Error B']})
    error_dict2 = ValidationError({'field2': ['Error B'], 'field1': ['Error A']})
    assert error_dict1 == error_dict2, "ValidationErrors with same field errors in different order should be equal"
    
    # Test nested ValidationError equality
    nested1 = ValidationError({
        'field1': ValidationError(['Error A', 'Error B']),
        'field2': ValidationError('Error C')
    })
    nested2 = ValidationError({
        'field2': ValidationError('Error C'),
        'field1': ValidationError(['Error B', 'Error A'])
    })
    assert nested1 == nested2, "Nested ValidationErrors with same content in different order should be equal"
    
    # Test hashability - ValidationErrors should be hashable if they have consistent attributes
    try:
        hash_set = {error1, error2}
        assert len(hash_set) == 1, "Equal ValidationErrors should have the same hash"
    except TypeError:
        pytest.fail("ValidationError instances should be hashable")
    
    # Test hash consistency for complex ValidationErrors
    try:
        complex_hash_set = {error_list1, error_list2}
        assert len(complex_hash_set) == 1, "Equal complex ValidationErrors should have the same hash"
    except TypeError:
        pytest.fail("Complex ValidationError instances should be hashable")