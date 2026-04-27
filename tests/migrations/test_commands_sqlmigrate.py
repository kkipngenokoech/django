import io
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings


class SqlMigrateTests(TestCase):
    @override_settings(MIGRATION_MODULES={"migrations": "migrations.test_migrations"})
    def test_issue_reproduction(self):
        """
        Test that sqlmigrate doesn't wrap output in BEGIN/COMMIT when
        the database doesn't support transactional DDL, even if the migration is atomic.
        """
        out = io.StringIO()
        
        # Mock can_rollback_ddl to False to simulate a database that doesn't support transactional DDL
        with mock.patch('django.db.connection.features.can_rollback_ddl', False):
            call_command('sqlmigrate', 'migrations', '0001', stdout=out, no_color=True)
        
        output = out.getvalue()
        
        # The bug: output should NOT contain BEGIN/COMMIT when can_rollback_ddl is False
        # but currently it does because sqlmigrate only checks migration.atomic
        assert 'BEGIN;' not in output, f"Output should not contain BEGIN when can_rollback_ddl=False, but got: {output}"
        assert 'COMMIT;' not in output, f"Output should not contain COMMIT when can_rollback_ddl=False, but got: {output}"