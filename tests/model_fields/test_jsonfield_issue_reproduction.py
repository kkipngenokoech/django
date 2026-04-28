import pytest
from django.test import TestCase, skipUnlessDBFeature
from django.db import connection
from .models import NullableJSONModel


@skipUnlessDBFeature('supports_json_field')
class TestIssueReproduction(TestCase):
    def test_issue_reproduction(self):
        """Test that __isnull=True on KeyTransform should not match JSON null values."""
        # Create test objects
        obj_no_key = NullableJSONModel.objects.create(value={'a': 'b'})  # No 'j' key
        obj_json_null = NullableJSONModel.objects.create(value={'j': None})  # Has 'j' key with JSON null
        obj_with_value = NullableJSONModel.objects.create(value={'j': 'some_value'})  # Has 'j' key with value
        obj_sql_null = NullableJSONModel.objects.create(value=None)  # SQL NULL
        
        # Query for objects where 'j' key is null
        result = list(NullableJSONModel.objects.filter(value__j__isnull=True))
        
        # Should only match objects that don't have the 'j' key at all, plus SQL NULL
        expected = [obj_no_key, obj_sql_null]
        
        # On SQLite and Oracle, this incorrectly also includes obj_json_null
        # The test will fail on those backends because obj_json_null is incorrectly included
        if connection.vendor in ('sqlite', 'oracle'):
            # This assertion will fail, demonstrating the bug
            self.assertEqual(len(result), 2, 
                f"Expected 2 objects but got {len(result)}. "
                f"Bug: JSON null values are incorrectly matched on {connection.vendor}")
            self.assertNotIn(obj_json_null, result, 
                f"Object with JSON null should not match __isnull=True on {connection.vendor}")
        
        self.assertIn(obj_no_key, result)
        self.assertIn(obj_sql_null, result)
        self.assertNotIn(obj_with_value, result)