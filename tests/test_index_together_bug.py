import pytest
from django.db import models, connection
from django.db.migrations.state import ProjectState
from django.db.migrations.operations import AlterIndexTogether
from django.test import TransactionTestCase


class TestModel(models.Model):
    field1 = models.CharField(max_length=100)
    field2 = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'
        unique_together = [('field1', 'field2')]
        index_together = [('field1', 'field2')]


def test_issue_reproduction():
    """Test that deleting index_together fails when unique_together exists on same fields."""
    # Create the table with both unique_together and index_together
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(TestModel)
    
    try:
        # Create project states for migration
        old_state = ProjectState()
        old_state.add_model(TestModel)
        
        # Create new model without index_together but keeping unique_together
        class NewTestModel(models.Model):
            field1 = models.CharField(max_length=100)
            field2 = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'test_app'
                unique_together = [('field1', 'field2')]
                # index_together removed
        
        new_state = ProjectState()
        new_state.add_model(NewTestModel)
        
        # Create the migration operation to remove index_together
        operation = AlterIndexTogether(
            name='TestModel',
            index_together=set(),  # Remove index_together
        )
        
        # This should fail with ValueError about finding wrong number of constraints
        with connection.schema_editor() as schema_editor:
            operation.database_forwards('test_app', schema_editor, old_state, new_state)
            
    finally:
        # Clean up
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(TestModel)