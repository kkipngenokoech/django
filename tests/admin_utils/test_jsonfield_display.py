import json
from django.contrib.admin.utils import display_for_field
from django.db import models
from django.test import TestCase


class JSONField(models.JSONField):
    """Mock JSONField for testing"""
    pass


def test_issue_reproduction():
    """Test that JSONField values are displayed as valid JSON, not Python dict representation."""
    field = JSONField()
    test_value = {"foo": "bar"}
    empty_value_display = "-"
    
    result = display_for_field(test_value, field, empty_value_display)
    
    # The bug: result will be "{'foo': 'bar'}" (Python dict representation)
    # Expected: '{"foo": "bar"}' (valid JSON)
    assert result == '{"foo": "bar"}', f"Expected valid JSON, got: {result}"