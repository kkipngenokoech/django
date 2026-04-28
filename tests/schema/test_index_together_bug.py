import pytest
from django.db import models, connection
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.test import TestCase
from django.test.utils import isolate_apps


def test_issue_reproduction():
    """Test that deleting index_together fails when unique_together exists on same fields."""
    
    # Create a test model with both unique_together and index_together on same fields
    @isolate_apps('test_app')
    class TestModel(models.Model):
        field1 = models.CharField(max_length=100)
        field2 = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test_app'
            db_table = 'test_model_table'
            unique_together = [('field1', 'field2')]
            index_together = [('field1', 'field2')]
    
    # Create the schema editor
    with connection.schema_editor() as schema_editor:
        # Create the model table first
        schema_editor.create_model(TestModel)
        
        # Now try to remove index_together while keeping unique_together
        # This should fail with ValueError about finding wrong number of constraints
        old_index_together = [('field1', 'field2')]
        new_index_together = []
        
        with pytest.raises(ValueError, match=r"Found wrong number \(2\) of constraints"):
            schema_editor.alter_index_together(
                TestModel, 
                old_index_together, 
                new_index_together
            )