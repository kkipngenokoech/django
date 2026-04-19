import pytest
from unittest.mock import patch
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from io import StringIO


def test_issue_reproduction():
    """Test that sqlmigrate doesn't wrap output in BEGIN/COMMIT when database doesn't support transactional DDL"""
    # Mock a database that doesn't support rollback DDL
    with patch.object(connection.features, 'can_rollback_ddl', False):
        # Create a StringIO to capture output
        out = StringIO()
        
        # Call sqlmigrate on an atomic migration (most migrations are atomic by default)
        # Using contenttypes 0001 which should exist in Django
        try:
            call_command('sqlmigrate', 'contenttypes', '0001', stdout=out)
            output = out.getvalue()
            
            # The bug: output should NOT contain BEGIN/COMMIT when can_rollback_ddl is False
            # But currently it does because sqlmigrate only checks migration.atomic
            assert 'BEGIN;' not in output, "sqlmigrate should not wrap output in BEGIN when database doesn't support transactional DDL"
            assert 'COMMIT;' not in output, "sqlmigrate should not wrap output in COMMIT when database doesn't support transactional DDL"
            
        except Exception as e:
            # If contenttypes migration doesn't exist, try auth instead
            out = StringIO()
            call_command('sqlmigrate', 'auth', '0001', stdout=out)
            output = out.getvalue()
            
            assert 'BEGIN;' not in output, "sqlmigrate should not wrap output in BEGIN when database doesn't support transactional DDL"
            assert 'COMMIT;' not in output, "sqlmigrate should not wrap output in COMMIT when database doesn't support transactional DDL"