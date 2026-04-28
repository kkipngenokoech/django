import pytest
from unittest.mock import patch, MagicMock
from django.core.management.sql import emit_post_migrate_signal
from django.apps import apps
from django.db import DEFAULT_DB_ALIAS
from django.test import TestCase, override_settings
from django.contrib.auth.management import create_permissions


def test_issue_reproduction():
    """Test that migrate command respects database parameter when creating permissions."""
    # Mock a custom database router that should NOT be called when using specific database
    mock_router = MagicMock()
    mock_router.db_for_read = MagicMock(return_value='wrong_db')
    mock_router.db_for_write = MagicMock(return_value='wrong_db')
    mock_router.allow_migrate_model = MagicMock(return_value=True)
    
    # Get a test app config
    app_config = apps.get_app_config('auth')
    
    # Patch the router to use our mock
    with patch('django.db.router.routers', [mock_router]):
        with patch('django.contrib.auth.management.router', mock_router):
            # This should use the specified database 'test_db' and NOT call the router for db selection
            create_permissions(
                app_config=app_config,
                verbosity=0,
                interactive=False,
                using='test_db',  # Specify a non-default database
                apps=apps
            )
    
    # The bug is that the router's db_for_read/db_for_write methods get called
    # even when we explicitly specify the database to use
    # This assertion will FAIL on buggy code because the router gets consulted
    assert not mock_router.db_for_read.called, "Router should not be consulted for database selection when 'using' parameter is specified"
    assert not mock_router.db_for_write.called, "Router should not be consulted for database selection when 'using' parameter is specified"