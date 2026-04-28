import pytest
from django.db import models, connection
from django.db.backends.sqlite3.schema import DatabaseSchemaEditor
from django.test import TestCase, override_settings
from django.apps.registry import Apps
from django.db import migrations
from django.db.migrations.state import ProjectState


def test_issue_reproduction():
    """Test that remaking a table with unique constraints works on SQLite."""
    # Skip if not using SQLite
    if connection.vendor != 'sqlite':
        pytest.skip("This test is specific to SQLite")
    
    # Create a test model with unique constraint
    class TestModel(models.Model):
        name = models.SlugField()
        value = models.CharField(max_length=200)
        
        class Meta:
            app_label = 'test_app'
            db_table = 'test_unique_constraint_model'
            constraints = [
                models.UniqueConstraint(
                    fields=['name', 'value'],
                    name='unique_name_value'
                )
            ]
    
    # Create the table initially
    with connection.schema_editor() as editor:
        editor.create_model(TestModel)
    
    try:
        # Now alter the field - this should trigger _remake_table with constraints
        old_field = TestModel._meta.get_field('value')
        new_field = models.CharField(max_length=150)  # Changed from 200 to 150
        new_field.set_attributes_from_name('value')
        
        # This should fail on the current buggy code due to constraint handling issues
        with connection.schema_editor() as editor:
            editor.alter_field(TestModel, old_field, new_field)
            
    finally:
        # Clean up - drop the table
        with connection.schema_editor() as editor:
            editor.delete_model(TestModel)