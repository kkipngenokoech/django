import pytest
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.test import TestCase, override_settings
from django.test.utils import isolate_apps


class TestRouter:
    """Router that only allows migrations on 'default' database."""
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'


@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        },
        'other': {
            'ENGINE': 'django.db.backends.sqlite3', 
            'NAME': ':memory:',
        }
    },
    DATABASE_ROUTERS=['test_migration_recorder.TestRouter']
)
def test_issue_reproduction():
    """Test that MigrationRecorder respects db_router allow_migrate rules."""
    from django.db import connections
    
    # Get connection to 'other' database where migrations should not be allowed
    other_connection = connections['other']
    recorder = MigrationRecorder(other_connection)
    
    # This should not create the django_migrations table on 'other' db
    # because the router disallows migrations on non-default databases
    recorder.ensure_schema()
    
    # The test fails because ensure_schema() creates the table regardless of router rules
    assert not recorder.has_table(), "MigrationRecorder should not create table when router disallows migrations"