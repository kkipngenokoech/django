import pytest
from django.db import models, connection
from django.db.backends.sqlite3.schema import DatabaseSchemaEditor
from django.test import TestCase, override_settings
from django.apps import apps
from django.db.migrations.state import ProjectState


def test_issue_reproduction():
    """Test that remaking a table with unique constraints works on SQLite."""
    
    # Create a test model with unique constraint
    class TestModel(models.Model):
        name = models.SlugField()
        value = models.CharField(max_length=200)
        
        class Meta:
            app_label = 'test_app'
            db_table = 'test_remake_table'
            constraints = [
                models.UniqueConstraint(
                    fields=['name', 'value'],
                    name='unique_name_value'
                )
            ]
    
    # Only run this test on SQLite
    if connection.vendor != 'sqlite':
        pytest.skip('This test is specific to SQLite')
    
    with connection.schema_editor() as editor:
        # Create the initial table
        editor.create_model(TestModel)
        
        # Create a modified field (this triggers table remake)
        old_field = TestModel._meta.get_field('value')
        new_field = models.CharField(max_length=150)  # Changed from 200 to 150
        new_field.set_attributes_from_name('value')
        
        # This should crash on the current buggy code when trying to remake
        # the table because unique constraints are not properly handled
        editor._remake_table(TestModel, alter_field=(old_field, new_field))
        
        # Clean up
        editor.delete_model(TestModel)