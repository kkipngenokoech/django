import pytest
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState
from django.test import TestCase


def test_issue_reproduction():
    """Test that ForeignKey to_field is updated when referenced primary key is renamed."""
    
    # Create initial state with ModelA having a primary key field and ModelB with FK to it
    class ModelA(models.Model):
        field_wrong = models.CharField('field1', max_length=50, primary_key=True)
        
        class Meta:
            app_label = 'testapp'
    
    class ModelB(models.Model):
        field_fk = models.ForeignKey(ModelA, blank=True, null=True, on_delete=models.CASCADE, to_field='field_wrong')
        
        class Meta:
            app_label = 'testapp'
    
    # Create the "from" state
    from_state = ProjectState()
    from_state.add_model(ModelA._meta.get_field('field_wrong').model._state.add_to_state(from_state))
    from_state.add_model(ModelB._meta.get_field('field_fk').model._state.add_to_state(from_state))
    
    # Create the "to" state with renamed primary key
    class ModelARenamed(models.Model):
        field_fixed = models.CharField('field1', max_length=50, primary_key=True)
        
        class Meta:
            app_label = 'testapp'
            db_table = ModelA._meta.db_table  # Same table name
    
    class ModelBUpdated(models.Model):
        field_fk = models.ForeignKey(ModelARenamed, blank=True, null=True, on_delete=models.CASCADE, to_field='field_fixed')
        
        class Meta:
            app_label = 'testapp'
            db_table = ModelB._meta.db_table  # Same table name
    
    to_state = ProjectState()
    to_state.add_model(ModelARenamed._meta.get_field('field_fixed').model._state.add_to_state(to_state))
    to_state.add_model(ModelBUpdated._meta.get_field('field_fk').model._state.add_to_state(to_state))
    
    # Run autodetector
    autodetector = MigrationAutodetector(from_state, to_state)
    changes = autodetector.changes(graph=None)
    
    # Check that the generated migration operations include proper to_field update
    operations = changes.get('testapp', [])
    
    # Find the AlterField operation for the ForeignKey
    alter_field_ops = [op for migration in operations for op in migration.operations 
                      if hasattr(op, 'name') and op.name == 'field_fk' and 
                      hasattr(op, 'field') and hasattr(op.field, 'remote_field')]
    
    # The bug: to_field should be 'field_fixed' but it's still 'field_wrong'
    assert len(alter_field_ops) > 0, "Should have AlterField operation for ForeignKey"
    fk_field = alter_field_ops[0].field
    
    # This assertion will FAIL on buggy code because to_field will be 'field_wrong'
    assert fk_field.remote_field.to_fields == ('field_fixed',), f"Expected to_field='field_fixed', got {fk_field.remote_field.to_fields}"