import json
from django.contrib.admin.utils import display_for_field
from django.contrib.postgres.fields import JSONField
from django.test import TestCase


def test_issue_reproduction():
    """Test that JSONField values are properly displayed as valid JSON in admin readonly fields."""
    # Create a JSONField instance
    json_field = JSONField()
    
    # Test data that should be displayed as valid JSON
    test_data = {"foo": "bar", "nested": {"key": "value"}, "list": [1, 2, 3]}
    
    # Get the display value using the current implementation
    display_value = display_for_field(test_data, json_field, "")
    
    # The current implementation returns str(value) which gives Python dict representation
    # This should be valid JSON instead
    try:
        # Try to parse the display value as JSON - this should work but currently fails
        json.loads(display_value)
        # If we get here, the display value is valid JSON (which is what we want)
        assert True
    except (json.JSONDecodeError, TypeError):
        # Current buggy behavior - display_value is not valid JSON
        # It's likely something like "{'foo': 'bar', 'nested': {'key': 'value'}, 'list': [1, 2, 3]}"
        # which uses single quotes and is not valid JSON
        assert False, f"JSONField display value is not valid JSON: {display_value}"
    
    # Also test that the display value matches the expected JSON format
    expected_json = json.dumps(test_data, sort_keys=True)
    # The display should be valid JSON that represents the same data
    parsed_display = json.loads(display_value)
    assert parsed_display == test_data, f"Display value {display_value} does not match original data {test_data}"