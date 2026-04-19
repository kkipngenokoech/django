import pytest
from django.db import connection
from django.test.utils import setup_test_environment, teardown_test_environment
from django.test import override_settings
from django.db.backends.base.creation import BaseDatabaseCreation


def test_issue_reproduction():
    """Test that serialize_db_to_string fails when MIGRATE is False."""
    # Mock a database configuration with MIGRATE: False
    test_settings = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'TEST': {
                'MIGRATE': False
            }
        }
    }
    
    with override_settings(DATABASES=test_settings):
        creation = BaseDatabaseCreation(connection)
        
        # This should fail because tables don't exist when MIGRATE is False
        # but serialize_db_to_string tries to query them anyway
        with pytest.raises(Exception):
            creation.serialize_db_to_string()