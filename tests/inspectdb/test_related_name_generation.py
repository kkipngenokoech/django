import io
import sys
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings


class InspectdbRelatedNameTest(TransactionTestCase):
    def setUp(self):
        # Create tables with multiple foreign keys to the same target
        with connection.cursor() as cursor:
            # Create target table
            cursor.execute(
                "CREATE TABLE target_table (id INTEGER PRIMARY KEY, name VARCHAR(50))"
            )
            # Create source table with two foreign keys to target_table
            cursor.execute(
                "CREATE TABLE source_table ("
                "id INTEGER PRIMARY KEY, "
                "field1_id INTEGER REFERENCES target_table(id), "
                "field2_id INTEGER REFERENCES target_table(id)"
                ")"
            )

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS source_table")
            cursor.execute("DROP TABLE IF EXISTS target_table")

    def test_issue_reproduction(self):
        # Capture inspectdb output
        out = io.StringIO()
        call_command('inspectdb', 'source_table', 'target_table', stdout=out)
        generated_code = out.getvalue()
        
        # The generated code should contain ForeignKey fields without related_name
        # This will cause Django's E304 error when the models are used
        assert 'field1 = models.ForeignKey(' in generated_code
        assert 'field2 = models.ForeignKey(' in generated_code
        
        # Verify that no related_name is generated (this is the bug)
        assert 'related_name=' not in generated_code
        
        # Execute the generated code to create model classes
        namespace = {'models': __import__('django.db.models', fromlist=[''])}
        exec(generated_code, namespace)
        
        # Get the generated SourceTable model
        source_model = None
        for name, obj in namespace.items():
            if hasattr(obj, '_meta') and getattr(obj._meta, 'db_table', None) == 'source_table':
                source_model = obj
                break
        
        assert source_model is not None, "SourceTable model not found in generated code"
        
        # Trigger Django's model validation which should raise E304 error
        from django.core.checks import run_checks
        from django.apps import apps
        
        # Temporarily register the model
        app_config = apps.get_app_config('contenttypes')  # Use existing app
        original_models = app_config.models.copy()
        
        try:
            # Add our generated model to trigger validation
            model_name = source_model.__name__.lower()
            app_config.models[model_name] = source_model
            source_model._meta.apps = apps
            source_model._meta.app_label = 'contenttypes'
            
            # Run Django's system checks - this should fail with E304
            errors = run_checks()
            
            # Look for the specific E304 error about clashing reverse accessors
            e304_errors = [e for e in errors if e.id == 'fields.E304']
            assert len(e304_errors) > 0, f"Expected E304 error not found. Errors: {[e.id for e in errors]}"
            
            # Verify the error message mentions clashing reverse accessors
            error_msg = str(e304_errors[0])
            assert 'clashes with reverse accessor' in error_msg
            
        finally:
            # Restore original models
            app_config.models = original_models