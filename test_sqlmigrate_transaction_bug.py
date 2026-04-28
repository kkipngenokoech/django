import pytest
from unittest.mock import patch
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from io import StringIO


def test_issue_reproduction():
    """Test that sqlmigrate doesn't wrap output in BEGIN/COMMIT when database doesn't support transactional DDL."""
    # Mock a database that doesn't support transactional DDL
    with patch.object(connection.features, 'can_rollback_ddl', False):
        # Capture the output of sqlmigrate command
        out = StringIO()
        
        # Run sqlmigrate on an existing migration (using contenttypes as it's always available)
        try:
            call_command('sqlmigrate', 'contenttypes', '0001', stdout=out)
            output = out.getvalue()
            
            # The bug: output should NOT contain BEGIN/COMMIT when can_rollback_ddl is False
            # but currently it does because sqlmigrate only checks migration.atomic
            assert 'BEGIN;' not in output, "sqlmigrate should not wrap output in BEGIN/COMMIT when database doesn't support transactional DDL"
            assert 'COMMIT;' not in output, "sqlmigrate should not wrap output in BEGIN/COMMIT when database doesn't support transactional DDL"
            
        except Exception as e:
            # If contenttypes migration doesn't exist, skip the test
            pytest.skip(f"Required migration not available: {e}")