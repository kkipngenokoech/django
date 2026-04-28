import os
import tempfile
from django.db import connections
from django.test import TestCase, override_settings
from django.test.utils import setup_test_environment, teardown_test_environment
from django.core.management import call_command
from django.contrib.auth.models import User
from admin_views.models import Book


def test_issue_reproduction():
    """Test that persistent SQLite databases don't cause locking issues in multidb scenarios."""
    # Create temporary database files
    temp_dir = tempfile.mkdtemp()
    default_db = os.path.join(temp_dir, 'test_default.sqlite3')
    other_db = os.path.join(temp_dir, 'test_other.sqlite3')
    
    databases_config = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'TEST': {
                'NAME': default_db
            },
        },
        'other': {
            'ENGINE': 'django.db.backends.sqlite3', 
            'NAME': ':memory:',
            'TEST': {
                'NAME': other_db
            },
        }
    }
    
    with override_settings(DATABASES=databases_config):
        # Setup test environment
        setup_test_environment()
        
        try:
            # Create test databases with keepdb=True to simulate persistent databases
            for alias in ['default', 'other']:
                connection = connections[alias]
                creation = connection.creation
                # This should trigger the database locking issue
                test_db_name = creation._create_test_db(verbosity=1, autoclobber=True, keepdb=True)
                
                # Try to perform operations that would cause locking
                call_command('migrate', verbosity=0, interactive=False, database=alias, run_syncdb=True)
                
                # Create some test data to ensure database operations work
                User.objects.using(alias).create_user(username=f'test_{alias}', password='test')
                Book.objects.using(alias).create(name=f'Test Book {alias}')
                
                # Force close connection to test locking behavior
                connection.close()
                
        finally:
            # Cleanup
            teardown_test_environment()
            # Remove temporary files
            for db_file in [default_db, other_db]:
                if os.path.exists(db_file):
                    os.remove(db_file)
            os.rmdir(temp_dir)