import pytest
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase
from io import StringIO


def test_issue_reproduction():
    """Test that sqlmigrate doesn't wrap output in BEGIN/COMMIT when database doesn't support transactional DDL."""
    # Mock can_rollback_ddl to False to simulate a database that doesn't support transactional DDL
    with patch('django.db.connection.features.can_rollback_ddl', False):
        out = StringIO()
        # Call sqlmigrate on an atomic migration (most migrations are atomic by default)
        # Using contenttypes initial migration as it's guaranteed to exist
        call_command('sqlmigrate', 'contenttypes', '0001', stdout=out)
        output = out.getvalue()
        
        # The bug: output should NOT contain BEGIN/COMMIT when can_rollback_ddl is False
        # But currently it does because sqlmigrate only checks migration.atomic
        assert 'BEGIN;' not in output, "sqlmigrate should not wrap output in BEGIN/COMMIT when database doesn't support transactional DDL"
        assert 'COMMIT;' not in output, "sqlmigrate should not wrap output in BEGIN/COMMIT when database doesn't support transactional DDL"