from django.core.exceptions import ValidationError
from django.test import TestCase


class ValidationErrorEqualityTest(TestCase):
    """Test ValidationError equality comparison."""

    def test_identical_messages_are_equal(self):
        """ValidationErrors with identical messages should be equal."""
        error1 = ValidationError('This field is required.')
        error2 = ValidationError('This field is required.')
        self.assertEqual(error1, error2)

    def test_different_messages_are_not_equal(self):
        """ValidationErrors with different messages should not be equal."""
        error1 = ValidationError('This field is required.')
        error2 = ValidationError('This field is invalid.')
        self.assertNotEqual(error1, error2)

    def test_same_messages_different_order_are_equal(self):
        """ValidationErrors with same messages in different order should be equal."""
        error1 = ValidationError(['Field A is required.', 'Field B is invalid.'])
        error2 = ValidationError(['Field B is invalid.', 'Field A is required.'])
        self.assertEqual(error1, error2)

    def test_multiple_messages_identical_are_equal(self):
        """ValidationErrors with identical multiple messages should be equal."""
        messages = ['This field is required.', 'This field must be unique.']
        error1 = ValidationError(messages)
        error2 = ValidationError(messages)
        self.assertEqual(error1, error2)

    def test_empty_messages_are_equal(self):
        """ValidationErrors with empty message lists should be equal."""
        error1 = ValidationError([])
        error2 = ValidationError([])
        self.assertEqual(error1, error2)

    def test_not_equal_to_non_validation_error(self):
        """ValidationError should not equal non-ValidationError objects."""
        error = ValidationError('This field is required.')
        self.assertNotEqual(error, 'This field is required.')
        self.assertNotEqual(error, Exception('This field is required.'))
        self.assertNotEqual(error, None)
        self.assertNotEqual(error, 42)

    def test_dict_based_errors_are_equal(self):
        """ValidationErrors with identical error dictionaries should be equal."""
        error_dict = {'field1': ['Error 1'], 'field2': ['Error 2']}
        error1 = ValidationError(error_dict)
        error2 = ValidationError(error_dict)
        self.assertEqual(error1, error2)

    def test_dict_based_errors_different_order_are_equal(self):
        """ValidationErrors with same dict errors in different field order should be equal."""
        error1 = ValidationError({'field1': ['Error 1'], 'field2': ['Error 2']})
        error2 = ValidationError({'field2': ['Error 2'], 'field1': ['Error 1']})
        self.assertEqual(error1, error2)

    def test_mixed_single_and_list_messages_are_equal(self):
        """ValidationErrors with equivalent single and list messages should be equal."""
        error1 = ValidationError('This field is required.')
        error2 = ValidationError(['This field is required.'])
        self.assertEqual(error1, error2)

    def test_nested_validation_errors_are_equal(self):
        """ValidationErrors containing other ValidationErrors should be equal."""
        inner_error = ValidationError('Inner error')
        error1 = ValidationError([inner_error, 'Outer error'])
        error2 = ValidationError([ValidationError('Inner error'), 'Outer error'])
        self.assertEqual(error1, error2)