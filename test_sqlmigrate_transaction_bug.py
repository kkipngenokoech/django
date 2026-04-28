import pytest
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase
from io import StringIO


def test_issue_reproduction():
    """Test that sqlmigrate doesn't wrap output in BEGIN/COMMIT when database doesn't support transactional DDL."""
    # Mock a database that doesn't support transactional DDL
    with patch('django.db.connections') as mock_connections:
        # Create a mock connection with can_rollback_ddl = False
        mock_connection = mock_connections.__getitem__.return_value
        mock_connection.features.can_rollback_ddl = False
        
        # Create a mock executor and migration
        mock_executor = mock_connection.return_value
        mock_executor.loader.migrated_apps = ['testapp']
        
        # Create a mock atomic migration
        mock_migration = type('Migration', (), {
            'atomic': True,  # This is atomic
            'name': '0001_initial'
        })()
        
        mock_executor.loader.get_migration_by_prefix.return_value = mock_migration
        mock_executor.loader.graph.nodes = {('testapp', '0001_initial'): mock_migration}
        mock_executor.collect_sql.return_value = ['CREATE TABLE test (id INTEGER);']
        
        # Mock apps.get_app_config to avoid LookupError
        with patch('django.apps.apps.get_app_config'):
            from django.core.management.commands.sqlmigrate import Command
            
            # Create command instance and call handle
            command = Command()
            output = command.handle(
                app_label='testapp',
                migration_name='0001_initial',
                database='default',
                backwards=False
            )
            
            # The bug: output_transaction should be False when can_rollback_ddl is False
            # But currently it's only checking migration.atomic
            # This assertion will FAIL on buggy code because output_transaction will be True
            assert command.output_transaction == False, "output_transaction should be False when database doesn't support transactional DDL"