import pytest
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState
from django.db.migrations.operations import AlterField, AlterUniqueTogether


def test_issue_reproduction():
    """Test that changing ForeignKey to ManyToManyField removes conflicting unique_together."""
    
    # Create initial state with ForeignKey and unique_together
    from_state = ProjectState()
    from_state.add_model(
        models.state.ModelState(
            'testapp',
            'ProjectDataSet',
            [
                ('id', models.AutoField(primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
        )
    )
    from_state.add_model(
        models.state.ModelState(
            'testapp',
            'Authors',
            [
                ('id', models.AutoField(primary_key=True)),
                ('project_data_set', models.ForeignKey('testapp.ProjectDataSet', on_delete=models.PROTECT)),
                ('state', models.IntegerField()),
                ('start_date', models.DateField()),
            ],
            options={'unique_together': [('project_data_set', 'state', 'start_date')]}
        )
    )
    
    # Create target state with ManyToManyField and no unique_together
    to_state = ProjectState()
    to_state.add_model(
        models.state.ModelState(
            'testapp',
            'ProjectDataSet',
            [
                ('id', models.AutoField(primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
        )
    )
    to_state.add_model(
        models.state.ModelState(
            'testapp',
            'Authors',
            [
                ('id', models.AutoField(primary_key=True)),
                ('project_data_set', models.ManyToManyField('testapp.ProjectDataSet')),
                ('state', models.IntegerField()),
                ('start_date', models.DateField()),
            ],
            options={}
        )
    )
    
    # Generate migrations
    autodetector = MigrationAutodetector(from_state, to_state)
    changes = autodetector.changes(graph=None)
    
    # Check that we have operations for the testapp
    assert 'testapp' in changes
    operations = changes['testapp'][0].operations
    
    # The bug: autodetector should generate AlterUniqueTogether to remove the constraint
    # BEFORE the AlterField operation, but it doesn't
    alter_unique_together_ops = [op for op in operations if isinstance(op, AlterUniqueTogether)]
    alter_field_ops = [op for op in operations if isinstance(op, AlterField)]
    
    # This should pass but fails due to the bug - no AlterUniqueTogether operation is generated
    assert len(alter_unique_together_ops) > 0, "Should generate AlterUniqueTogether to remove constraint"
    
    # And the AlterUniqueTogether should come before AlterField
    unique_together_index = operations.index(alter_unique_together_ops[0])
    alter_field_index = operations.index(alter_field_ops[0])
    assert unique_together_index < alter_field_index, "AlterUniqueTogether should come before AlterField"