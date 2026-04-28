import json
from django.contrib.admin.utils import display_for_field
from django.contrib.postgres.fields import JSONField
from django.test import TestCase


def test_issue_reproduction():
    """Test that JSONField values are properly displayed as valid JSON in admin readonly fields."""
    # Create a JSONField instance
    json_field = JSONField()
    
    # Test case 1: Simple dict should be displayed as valid JSON
    test_value = {"foo": "bar"}
    result = display_for_field(test_value, json_field, "")
    
    # The bug: result will be "{'foo': 'bar'}" (Python dict repr) instead of '{"foo": "bar"}' (valid JSON)
    # This assertion will FAIL on the current buggy code
    assert result == '{"foo": "bar"}', f"Expected valid JSON string, got: {result}"
    
    # Test case 2: More complex nested structure
    complex_value = {"users": [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]}
    result2 = display_for_field(complex_value, json_field, "")
    expected_json = json.dumps(complex_value, separators=(',', ':'))
    
    # This will also FAIL on current code as it returns Python repr instead of JSON
    assert result2 == expected_json, f"Expected valid JSON string, got: {result2}"
    
    # Test case 3: Ensure the result is actually valid JSON that can be parsed
    try:
        json.loads(result)
        json.loads(result2)
    except json.JSONDecodeError:
        assert False, "The display result should be valid JSON that can be parsed"