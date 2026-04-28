import pytest
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState
from django.db.migrations import operations


def test_issue_reproduction():
    """
    Test that renaming a primary key field doesn't generate unnecessary AlterField
    operations for ForeignKeys with incorrect to_field parameters.
    """
    # Create initial state with ModelA having field_wrong as PK and ModelB with FK to ModelA
    before_state = ProjectState()
    before_state.add_model(
        models.Model._meta.apps.get_model('contenttypes', 'ContentType')._state
    )
    
    # ModelA with original field name
    class ModelA(models.Model):
        field_wrong = models.CharField('field1', max_length=50, primary_key=True)
        
        class Meta:
            app_label = 'testapp'
    
    # ModelB with ForeignKey to ModelA
    class ModelB(models.Model):
        field_fk = models.ForeignKey(ModelA, blank=True, null=True, on_delete=models.CASCADE)
        
        class Meta:
            app_label = 'testapp'
    
    before_state.add_model(ModelA._meta)
    before_state.add_model(ModelB._meta)
    
    # Create after state with ModelA having renamed field
    after_state = ProjectState()
    after_state.add_model(
        models.Model._meta.apps.get_model('contenttypes', 'ContentType')._state
    )
    
    # ModelA with renamed field
    class ModelARenamed(models.Model):
        field_fixed = models.CharField('field1', max_length=50, primary_key=True)
        
        class Meta:
            app_label = 'testapp'
            db_table = ModelA._meta.db_table  # Same table name
    
    # ModelB unchanged (ForeignKey should still work after PK rename)
    class ModelBUnchanged(models.Model):
        field_fk = models.ForeignKey(ModelARenamed, blank=True, null=True, on_delete=models.CASCADE)
        
        class Meta:
            app_label = 'testapp'
            db_table = ModelB._meta.db_table  # Same table name
    
    after_state.add_model(ModelARenamed._meta)
    after_state.add_model(ModelBUnchanged._meta)
    
    # Run autodetector
    autodetector = MigrationAutodetector(before_state, after_state)
    changes = autodetector.changes(graph=None)
    
    # Should only have operations for testapp
    assert 'testapp' in changes
    operations_list = changes['testapp'][0].operations
    
    # Should have exactly one RenameField operation
    rename_operations = [op for op in operations_list if isinstance(op, operations.RenameField)]
    assert len(rename_operations) == 1
    
    rename_op = rename_operations[0]
    assert rename_op.model_name == 'modela'
    assert rename_op.old_name == 'field_wrong'
    assert rename_op.new_name == 'field_fixed'
    
    # The bug: should NOT have any AlterField operations for the ForeignKey
    # But currently it generates one with incorrect to_field pointing to old name
    alter_field_operations = [op for op in operations_list if isinstance(op, operations.AlterField)]
    
    # This assertion will FAIL on buggy code because it generates an AlterField
    # with to_field='field_wrong' instead of no AlterField at all
    assert len(alter_field_operations) == 0, f"Unexpected AlterField operations found: {alter_field_operations}"
    
    # If there are AlterField operations (which there shouldn't be), 
    # verify they have the wrong to_field to demonstrate the bug
    if alter_field_operations:
        for alter_op in alter_field_operations:
            if hasattr(alter_op.field, 'remote_field') and alter_op.field.remote_field:
                # This shows the bug - to_field points to old name 'field_wrong'
                assert getattr(alter_op.field.remote_field, 'to_field', None) == 'field_wrong'
                # It should be 'field_fixed' or None (since it's the PK)
                assert False, f"AlterField operation has wrong to_field: {alter_op.field.remote_field.to_field}"