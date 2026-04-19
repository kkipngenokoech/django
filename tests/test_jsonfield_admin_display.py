import json
from django.contrib.admin.utils import display_for_field
from django.db import models
from django.test import TestCase


def test_issue_reproduction():
    """Test that JSONField values are displayed as valid JSON in admin readonly fields."""
    # Create a mock JSONField
    class MockJSONField(models.JSONField):
        def __init__(self):
            # Minimal initialization to avoid database setup
            pass
    
    field = MockJSONField()
    test_value = {"foo": "bar"}
    empty_value_display = "-"
    
    # Call display_for_field which is used by admin for readonly fields
    result = display_for_field(test_value, field, empty_value_display)
    
    # The bug: result will be "{'foo': 'bar'}" (Python dict repr with single quotes)
    # Expected: '{"foo": "bar"}' (valid JSON with double quotes)
    
    # This assertion will FAIL on the current buggy code
    # because display_for_field doesn't handle JSONField specially
    # and falls back to str(value) which gives Python dict representation
    assert result == '{"foo": "bar"}', f"Expected valid JSON, got: {result}"
    
    # Verify it's actually valid JSON
    try:
        json.loads(result)
    except json.JSONDecodeError:
        raise AssertionError(f"Result is not valid JSON: {result}")