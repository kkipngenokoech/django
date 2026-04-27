import pytest
from unittest.mock import patch
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from io import StringIO


class TestSqlmigrateTransactionWrapping(TestCase):
    def test_issue_reproduction(self):
        """Test that sqlmigrate doesn't wrap output in BEGIN/COMMIT when database doesn't support transactional DDL"""
        # Mock can_rollback_ddl to False to simulate a database that doesn't support transactional DDL
        with patch.object(connection.features, 'can_rollback_ddl', False):
            # Capture the output of sqlmigrate for an atomic migration
            out = StringIO()
            # Use a built-in Django migration that is atomic
            call_command('sqlmigrate', 'auth', '0001', stdout=out)
            output = out.getvalue()
            
            # The bug: output should NOT contain BEGIN/COMMIT when can_rollback_ddl is False
            # But currently it does because sqlmigrate only checks migration.atomic
            assert 'BEGIN;' not in output, "sqlmigrate should not wrap output in BEGIN/COMMIT when database doesn't support transactional DDL"
            assert 'COMMIT;' not in output, "sqlmigrate should not wrap output in BEGIN/COMMIT when database doesn't support transactional DDL"