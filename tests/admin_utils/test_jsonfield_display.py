import json
from django.contrib.admin.utils import display_for_field
from django.contrib.postgres.fields import JSONField
from django.test import TestCase

def test_issue_reproduction():
    """Test that JSONField values are displayed as valid JSON when readonly in admin."""
    field = JSONField()
    test_value = {"foo": "bar"}
    
    # This should return valid JSON string, but currently returns Python dict string
    result = display_for_field(test_value, field, "")
    
    # The bug: result will be "{'foo': 'bar'}" (Python dict string)
    # Expected: result should be '{"foo": "bar"}' (valid JSON)
    assert result == json.dumps(test_value), f"Expected valid JSON, got: {result}"