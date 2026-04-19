import io
import tempfile
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.apps import apps
from django.core.checks import run_checks
from django.core.checks.registry import registry
from django.db import models


def test_issue_reproduction():
    """Test that inspectdb generates models with clashing reverse accessors."""
    # Create test tables with multiple foreign keys to same target
    with connection.cursor() as cursor:
        # Create target table
        cursor.execute("""
            CREATE TABLE test_target (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100)
            )
        """)
        
        # Create source table with two foreign keys to same target
        cursor.execute("""
            CREATE TABLE test_source (
                id INTEGER PRIMARY KEY,
                target1_id INTEGER REFERENCES test_target(id),
                target2_id INTEGER REFERENCES test_target(id)
            )
        """)
    
    try:
        # Capture inspectdb output
        out = io.StringIO()
        call_command('inspectdb', 'test_source', 'test_target', stdout=out)
        generated_code = out.getvalue()
        
        # Write generated models to a temporary file and import them
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(generated_code)
            f.flush()
            
            # Import the generated models module
            import importlib.util
            spec = importlib.util.spec_from_file_location("generated_models", f.name)
            generated_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(generated_module)
            
            # Get the TestSource model class
            test_source_model = getattr(generated_module, 'TestSource')
            
            # Create a temporary app config to register the model
            from django.apps.config import AppConfig
            from django.apps import apps
            
            class TempAppConfig(AppConfig):
                name = 'temp_app'
                verbose_name = 'Temp App'
                
                def ready(self):
                    pass
            
            # Register models with Django's app registry
            temp_app = TempAppConfig('temp_app', generated_module)
            apps.populate([temp_app])
            
            # Run Django's model validation checks
            errors = run_checks(include_deployment_checks=False)
            
            # Look for E304 error (clashing reverse accessors)
            e304_errors = [error for error in errors if error.id == 'fields.E304']
            
            # The test should fail because there ARE E304 errors (clashing reverse accessors)
            assert len(e304_errors) > 0, "Expected E304 errors for clashing reverse accessors, but none found"
            
    finally:
        # Clean up test tables
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS test_source")
            cursor.execute("DROP TABLE IF EXISTS test_target")