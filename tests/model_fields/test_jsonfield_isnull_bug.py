import pytest
from django.test import TestCase, skipUnlessDBFeature
from django.db import connection
from tests.model_fields.models import NullableJSONModel


@skipUnlessDBFeature('supports_json_field')
class TestIssueReproduction(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test objects with specific JSON structures
        cls.obj_no_key = NullableJSONModel.objects.create(value={'a': 'b'})  # No 'j' key
        cls.obj_null_value = NullableJSONModel.objects.create(value={'j': None})  # Has 'j' key with null value
        cls.obj_with_value = NullableJSONModel.objects.create(value={'j': 'some_value'})  # Has 'j' key with value
        cls.obj_sql_null = NullableJSONModel.objects.create(value=None)  # SQL NULL

    def test_issue_reproduction(self):
        # Test that value__j__isnull=True should only match objects without the 'j' key
        # It should NOT match objects that have the 'j' key with JSON null value
        result = list(NullableJSONModel.objects.filter(value__j__isnull=True))
        
        # Expected: only objects that don't have the 'j' key at all, plus SQL NULL
        expected = [self.obj_no_key, self.obj_sql_null]
        
        # On SQLite and Oracle, this incorrectly also includes obj_null_value
        # which has the key 'j' with JSON null value
        if connection.vendor in ['sqlite', 'oracle']:
            # This assertion will fail on buggy code because obj_null_value is incorrectly included
            self.assertEqual(set(result), set(expected))
        else:
            # On other databases, this should work correctly
            self.assertEqual(set(result), set(expected))