import pytest
from unittest.mock import patch
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from io import StringIO


class TestSqlmigrateTransactionWrapping(TestCase):
    
    def test_issue_reproduction(self):
        """Test that sqlmigrate doesn't wrap output in BEGIN/COMMIT when database doesn't support transactional DDL"""
        # Mock connection.features.can_rollback_ddl to False to simulate a database
        # that doesn't support transactional DDL (like MySQL with MyISAM)
        with patch.object(connection.features, 'can_rollback_ddl', False):
            # Use StringIO to capture the command output
            out = StringIO()
            
            # Call sqlmigrate on an atomic migration (most migrations are atomic by default)
            # We'll use the contenttypes app which should have migrations in any Django project
            try:
                call_command('sqlmigrate', 'contenttypes', '0001', stdout=out)
                output = out.getvalue()
                
                # The bug: current code wraps output in BEGIN/COMMIT even when
                # can_rollback_ddl is False. The correct behavior is to NOT wrap
                # when can_rollback_ddl is False, regardless of migration.atomic
                
                # This assertion will FAIL on buggy code because it incorrectly
                # includes BEGIN/COMMIT when can_rollback_ddl=False
                assert not output.strip().startswith('BEGIN;'), f"Output should not start with BEGIN when can_rollback_ddl=False, but got: {output[:100]}..."
                assert not output.strip().endswith('COMMIT;'), f"Output should not end with COMMIT when can_rollback_ddl=False, but got: ...{output[-100:]}"
                
            except Exception as e:
                # If contenttypes migrations don't exist, try auth app
                out = StringIO()
                call_command('sqlmigrate', 'auth', '0001', stdout=out)
                output = out.getvalue()
                
                # Same assertions - should fail on buggy code
                assert not output.strip().startswith('BEGIN;'), f"Output should not start with BEGIN when can_rollback_ddl=False, but got: {output[:100]}..."
                assert not output.strip().endswith('COMMIT;'), f"Output should not end with COMMIT when can_rollback_ddl=False, but got: ...{output[-100:]}"
        
        # Also test that when can_rollback_ddl=True, BEGIN/COMMIT should be included for atomic migrations
        with patch.object(connection.features, 'can_rollback_ddl', True):
            out = StringIO()
            try:
                call_command('sqlmigrate', 'contenttypes', '0001', stdout=out)
                output = out.getvalue()
                
                # When can_rollback_ddl=True and migration is atomic, should have BEGIN/COMMIT
                assert output.strip().startswith('BEGIN;'), f"Output should start with BEGIN when can_rollback_ddl=True, but got: {output[:100]}..."
                assert output.strip().endswith('COMMIT;'), f"Output should end with COMMIT when can_rollback_ddl=True, but got: ...{output[-100:]}"
                
            except Exception as e:
                out = StringIO()
                call_command('sqlmigrate', 'auth', '0001', stdout=out)
                output = out.getvalue()
                
                assert output.strip().startswith('BEGIN;'), f"Output should start with BEGIN when can_rollback_ddl=True, but got: {output[:100]}..."
                assert output.strip().endswith('COMMIT;'), f"Output should end with COMMIT when can_rollback_ddl=True, but got: ...{output[-100:]}"
