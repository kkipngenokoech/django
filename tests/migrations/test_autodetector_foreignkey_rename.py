import pytest
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState
from django.test import TestCase


def test_issue_reproduction():
    """
    Test that ForeignKey to_field parameter is updated when referenced primary key is renamed.
    """
    # Create initial state with ModelA having field_wrong as PK and ModelB with FK to ModelA
    initial_state = ProjectState()
    initial_state.add_model(
        models.Model._meta.apps.get_model('contenttypes', 'ContentType')._state
    )
    
    # Add ModelA with field_wrong as primary key
    model_a_initial = initial_state.add_model(
        type('ModelA', (models.Model,), {
            'field_wrong': models.CharField(max_length=50, primary_key=True),
            '__module__': 'test_app.models',
            'Meta': type('Meta', (), {'app_label': 'test_app'})
        })._state
    )
    
    # Add ModelB with ForeignKey to ModelA (implicitly references field_wrong)
    model_b_initial = initial_state.add_model(
        type('ModelB', (models.Model,), {
            'field_fk': models.ForeignKey('test_app.ModelA', blank=True, null=True, on_delete=models.CASCADE),
            '__module__': 'test_app.models', 
            'Meta': type('Meta', (), {'app_label': 'test_app'})
        })._state
    )
    
    # Create final state with ModelA having field_fixed as PK (renamed from field_wrong)
    final_state = ProjectState()
    final_state.add_model(
        models.Model._meta.apps.get_model('contenttypes', 'ContentType')._state
    )
    
    # Add ModelA with field_fixed as primary key (renamed)
    model_a_final = final_state.add_model(
        type('ModelA', (models.Model,), {
            'field_fixed': models.CharField(max_length=50, primary_key=True),
            '__module__': 'test_app.models',
            'Meta': type('Meta', (), {'app_label': 'test_app'})
        })._state
    )
    
    # Add ModelB with same ForeignKey (should now reference field_fixed)
    model_b_final = final_state.add_model(
        type('ModelB', (models.Model,), {
            'field_fk': models.ForeignKey('test_app.ModelA', blank=True, null=True, on_delete=models.CASCADE),
            '__module__': 'test_app.models',
            'Meta': type('Meta', (), {'app_label': 'test_app'})
        })._state
    )
    
    # Run autodetector
    autodetector = MigrationAutodetector(initial_state, final_state)
    changes = autodetector.changes(graph=None)
    
    # Check that we have migrations for test_app
    assert 'test_app' in changes
    migrations = changes['test_app']
    
    # Find the AlterField operation for ModelB's field_fk
    alter_field_op = None
    for migration in migrations:
        for operation in migration.operations:
            if (hasattr(operation, 'model_name') and 
                operation.model_name.lower() == 'modelb' and
                hasattr(operation, 'name') and 
                operation.name == 'field_fk' and
                operation.__class__.__name__ == 'AlterField'):
                alter_field_op = operation
                break
    
    # The bug: to_field should be 'field_fixed' but it's 'field_wrong'
    assert alter_field_op is not None, "AlterField operation for ModelB.field_fk not found"
    
    # This assertion will FAIL on buggy code because to_field will be 'field_wrong'
    # instead of 'field_fixed'
    field_kwargs = alter_field_op.field.deconstruct()[3]
    assert field_kwargs.get('to_field') == 'field_fixed', f"Expected to_field='field_fixed', got to_field='{field_kwargs.get('to_field')}'"
