import pytest
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.test import TestCase, override_settings
from django.db import router


class TestRouter:
    """Test router that disallows migrations on non-default databases."""
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'default':
            return True
        return False


def test_issue_reproduction():
    """Test that MigrationRecorder respects db_router allow_migrate rules."""
    # Create a test connection alias that simulates a non-default database
    test_db_alias = 'test_other_db'
    
    # Mock a connection for the test database
    from django.db import connections
    from django.db.backends.sqlite3.base import DatabaseWrapper
    
    # Create a mock connection that simulates another database
    mock_connection = connection.__class__({
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }, test_db_alias)
    
    # Temporarily add our test router
    original_routers = router.routers[:]
    router.routers = [TestRouter()]
    
    try:
        # Create MigrationRecorder for the non-default database
        recorder = MigrationRecorder(mock_connection)
        
        # This should respect the router's allow_migrate=False for non-default db
        # Currently this will create the table anyway, which is the bug
        with pytest.raises(Exception):  # Should raise an exception or handle gracefully
            recorder.ensure_schema()
            
    finally:
        # Restore original routers
        router.routers = original_routers