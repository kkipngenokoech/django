import pytest
from django.db import migrations, models
from django.db.migrations.writer import MigrationWriter
from django.apps import apps
from django.test import TestCase


def test_issue_reproduction():
    """Test that migration writer includes models import when models.Model appears in bases."""
    
    # Create a mock migration that has the problematic CreateModel operation
    # This simulates the scenario from the issue where we have:
    # bases=(app.models.MyMixin, models.Model)
    class MockMixin:
        pass
    
    operation = migrations.CreateModel(
        name='MyModel',
        fields=[
            ('name', models.TextField(primary_key=True)),
        ],
        options={
            'abstract': False,
        },
        bases=(MockMixin, models.Model),  # This should trigger the models import
    )
    
    # Create a mock migration
    class MockMigration:
        app_label = 'testapp'
        name = '0001_initial'
        operations = [operation]
        dependencies = []
        replaces = None
        initial = True
    
    # Generate the migration code
    writer = MigrationWriter(MockMigration())
    migration_code = writer.as_string()
    
    # The bug: migration code should be valid Python
    # It should either import models or use migrations.Model instead of models.Model
    # Currently it generates: bases=(..., models.Model) without importing models
    
    # Try to compile the generated code - this should not raise NameError
    # but currently it will because 'models' is not defined
    try:
        compile(migration_code, '<migration>', 'exec')
        # If we get here, the bug is fixed
    except NameError as e:
        if "name 'models' is not defined" in str(e):
            # This is the expected failure - the bug is present
            pytest.fail(f"Migration code is invalid Python due to missing models import: {e}")
        else:
            # Some other NameError, re-raise
            raise