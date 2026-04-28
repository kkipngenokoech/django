import pytest
from django.db import models
from django.db.migrations.operations.models import RenameModel
from django.db.migrations.state import ProjectState, ModelState
from django.test import TestCase
from unittest.mock import Mock


def test_issue_reproduction():
    """Test that RenameModel with db_table should be a noop."""
    # Create a mock schema editor to track database operations
    schema_editor = Mock()
    schema_editor.connection.alias = 'default'
    
    # Create initial state with a model that has custom db_table
    from_state = ProjectState()
    from_state.add_model(ModelState(
        app_label='testapp',
        name='OldModel',
        fields=[
            ('id', models.AutoField(primary_key=True)),
            ('name', models.CharField(max_length=100)),
        ],
        options={'db_table': 'custom_table_name'},
        bases=(models.Model,),
        managers=[],
    ))
    
    # Create target state with renamed model but same db_table
    to_state = ProjectState()
    to_state.add_model(ModelState(
        app_label='testapp',
        name='NewModel',
        fields=[
            ('id', models.AutoField(primary_key=True)),
            ('name', models.CharField(max_length=100)),
        ],
        options={'db_table': 'custom_table_name'},
        bases=(models.Model,),
        managers=[],
    ))
    
    # Create RenameModel operation
    operation = RenameModel(old_name='OldModel', new_name='NewModel')
    
    # Execute the database_forwards method
    operation.database_forwards('testapp', schema_editor, from_state, to_state)
    
    # The bug: currently this calls schema_editor.alter_db_table even when db_table is custom
    # It should be a noop and not call any schema_editor methods
    # This assertion will FAIL on current buggy code because alter_db_table gets called
    assert not schema_editor.alter_db_table.called, "RenameModel with custom db_table should not call alter_db_table"