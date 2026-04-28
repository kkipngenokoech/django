import io
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import override_settings


class InspectdbRelatedNameTest(TestCase):
    def test_issue_reproduction(self):
        """Test that inspectdb generates models with clashing reverse accessors."""
        # Create tables with multiple foreign keys to the same table
        with connection.cursor() as cursor:
            # Create a referenced table
            cursor.execute(
                "CREATE TABLE test_user (id INTEGER PRIMARY KEY, name VARCHAR(50))"
            )
            
            # Create a table with multiple FKs to the same table
            cursor.execute(
                "CREATE TABLE test_order ("
                "id INTEGER PRIMARY KEY, "
                "customer_id INTEGER, "
                "salesperson_id INTEGER"
                ")"
            )
        
        try:
            # Capture the output of inspectdb
            out = io.StringIO()
            call_command('inspectdb', 'test_order', 'test_user', stdout=out)
            output = out.getvalue()
            
            # Check that the generated code has multiple ForeignKey fields to the same model
            # without related_name, which would cause the clash
            assert 'customer = models.ForeignKey(' in output
            assert 'salesperson = models.ForeignKey(' in output
            
            # The bug is that there's no related_name generated, so both fields
            # would create clashing reverse accessors on TestUser
            # This should fail because the generated code would cause Django errors
            assert 'related_name=' not in output, "Bug: inspectdb should generate related_name but doesn't"
            
        finally:
            # Clean up the test tables
            with connection.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS test_order")
                cursor.execute("DROP TABLE IF EXISTS test_user")