import json
from django.contrib.admin.utils import display_for_field
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.test import TestCase


class TestModel(models.Model):
    json_data = JSONField()
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that JSONField values are displayed as valid JSON in admin readonly fields."""
    field = TestModel._meta.get_field('json_data')
    test_value = {'foo': 'bar', 'nested': {'key': 'value'}}
    
    result = display_for_field(test_value, field, empty_value_display='-')
    
    # The bug: result will be "{'foo': 'bar', 'nested': {'key': 'value'}}" (Python dict string)
    # Expected: result should be '{"foo": "bar", "nested": {"key": "value"}}' (valid JSON)
    
    # This assertion will fail on the current buggy code
    assert result == json.dumps(test_value)
    
    # Verify it's actually valid JSON
    json.loads(result)