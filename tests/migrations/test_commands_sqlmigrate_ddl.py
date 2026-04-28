import pytest
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase
from io import StringIO


def test_issue_reproduction():
    """Test that sqlmigrate doesn't wrap output in BEGIN/COMMIT when database doesn't support transactional DDL."""
    # Mock a database connection that doesn't support transactional DDL
    with patch('django.core.management.commands.sqlmigrate.connections') as mock_connections:
        # Create a mock connection with can_rollback_ddl = False
        mock_connection = mock_connections.__getitem__.return_value
        mock_connection.features.can_rollback_ddl = False
        
        # Mock the executor and migration
        with patch('django.core.management.commands.sqlmigrate.MigrationExecutor') as mock_executor_class:
            mock_executor = mock_executor_class.return_value
            
            # Mock a migration that is atomic
            mock_migration = mock_executor.loader.get_migration_by_prefix.return_value
            mock_migration.atomic = True
            mock_migration.name = 'test_migration'
            
            # Mock the loader
            mock_executor.loader.migrated_apps = ['testapp']
            mock_executor.loader.graph.nodes = {('testapp', 'test_migration'): mock_migration}
            
            # Mock collect_sql to return some SQL without BEGIN/COMMIT
            mock_executor.collect_sql.return_value = ['CREATE TABLE test (id INTEGER);']
            
            # Mock apps.get_app_config to avoid LookupError
            with patch('django.core.management.commands.sqlmigrate.apps.get_app_config'):
                # Capture the output
                out = StringIO()
                call_command('sqlmigrate', 'testapp', 'test_migration', stdout=out)
                output = out.getvalue()
                
                # The bug: output should NOT contain BEGIN/COMMIT when can_rollback_ddl is False
                # But current code will include them because it only checks migration.atomic
                assert 'BEGIN;' not in output, "Output should not contain BEGIN when database doesn't support transactional DDL"
                assert 'COMMIT;' not in output, "Output should not contain COMMIT when database doesn't support transactional DDL"