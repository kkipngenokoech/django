import json
import pytest
from django.test import TestCase
from django.db import models
from django.db.models.fields import json as json_fields


class TestModel(models.Model):
    data = json_fields.JSONField()
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that KeyTransformIsNull with isnull=True does not match JSON null values."""
    # Create test objects
    obj_no_key = TestModel(data={})
    obj_with_null = TestModel(data={'j': None})  # JSON null
    obj_with_value = TestModel(data={'j': 'value'})
    
    # Save objects to database
    TestModel.objects.all().delete()
    obj_no_key.save()
    obj_with_null.save() 
    obj_with_value.save()
    
    # Query for objects where key 'j' is null (should only match obj_no_key)
    result = list(TestModel.objects.filter(data__j__isnull=True))
    
    # This should only return obj_no_key, not obj_with_null
    # On SQLite/Oracle, this incorrectly includes obj_with_null
    assert len(result) == 1
    assert result[0].id == obj_no_key.id