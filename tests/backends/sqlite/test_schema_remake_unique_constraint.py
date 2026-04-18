import pytest
from django.db import models, connection
from django.db.backends.sqlite3.schema import DatabaseSchemaEditor
from django.test import TestCase
from django.apps import apps
from django.apps.registry import Apps


def test_issue_reproduction():
    """Test that remaking a table with unique constraints works on SQLite."""
    # Only run this test on SQLite
    if connection.vendor != 'sqlite':
        pytest.skip('This test is specific to SQLite')
    
    # Create a temporary app registry
    test_apps = Apps()
    
    # Define a model with unique constraint
    class TestModel(models.Model):
        name = models.SlugField(help_text="The tag key.")
        value = models.CharField(max_length=200, help_text="The tag value.")
        
        class Meta:
            app_label = 'test_app'
            db_table = 'test_tag'
            ordering = ["name", "value"]
            constraints = [
                models.UniqueConstraint(
                    "name",
                    "value", 
                    name="unique_name_value",
                )
            ]
            apps = test_apps
    
    # Register the model
    test_apps.register_model('test_app', TestModel)
    
    with DatabaseSchemaEditor(connection) as editor:
        # Create the initial table
        editor.create_model(TestModel)
        
        # Create a new field with different max_length to trigger remake
        old_field = TestModel._meta.get_field('value')
        new_field = models.CharField(max_length=150, help_text="The tag value.")
        new_field.set_attributes_from_name('value')
        
        # This should crash on the current buggy code due to unique constraint handling
        editor._remake_table(TestModel, alter_field=(old_field, new_field))
        
        # Clean up
        editor.delete_model(TestModel)