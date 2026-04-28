import pytest
from django.test import TestCase, override_settings
from django.db import connection
from django.db.backends.base.creation import BaseDatabaseCreation
from django.core.management import call_command
from django.conf import settings
from django.db.utils import ProgrammingError


def test_issue_reproduction():
    """Test that serialize_db_to_string fails when MIGRATE is False and django tables don't exist."""
    # Create a test database creation instance
    creation = BaseDatabaseCreation(connection)
    
    # Mock the database settings to have MIGRATE = False
    original_migrate = connection.settings_dict.get('TEST', {}).get('MIGRATE', True)
    
    try:
        # Set MIGRATE to False to reproduce the issue
        if 'TEST' not in connection.settings_dict:
            connection.settings_dict['TEST'] = {}
        connection.settings_dict['TEST']['MIGRATE'] = False
        
        # This should fail because django_admin_log and other Django tables don't exist
        # when migrations are skipped but serialize_db_to_string tries to access them
        with pytest.raises(ProgrammingError, match=r"relation .* does not exist"):
            creation.serialize_db_to_string()
            
    finally:
        # Restore original setting
        if 'TEST' in connection.settings_dict:
            connection.settings_dict['TEST']['MIGRATE'] = original_migrate