import os
import tempfile
from django.test import TestCase, override_settings
from django.db import connections
from django.contrib.auth.models import User
from admin_views.models import Book
from admin_views.test_multidb import Router


def test_issue_reproduction():
    """Test that reproduces SQLite database locking issue with persistent test databases."""
    # Create temporary database files to simulate persistent test databases
    with tempfile.TemporaryDirectory() as temp_dir:
        default_db = os.path.join(temp_dir, 'test_default.sqlite3')
        other_db = os.path.join(temp_dir, 'test_other.sqlite3')
        
        test_databases = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'TEST': {
                    'NAME': default_db
                },
            },
            'other': {
                'ENGINE': 'django.db.backends.sqlite3',
                'TEST': {
                    'NAME': other_db
                },
            }
        }
        
        with override_settings(DATABASES=test_databases, DATABASE_ROUTERS=['admin_views.test_multidb.Router']):
            # This should trigger the database locking issue when using persistent SQLite databases
            # The issue occurs when multiple connections to the same SQLite file are not properly managed
            
            # Simulate the multidb test scenario that fails
            for db in ['default', 'other']:
                Router.target_db = db
                
                # Create user in each database - this can cause locking issues
                user = User.objects.create_superuser(
                    username=f'admin_{db}', 
                    password='something', 
                    email=f'test_{db}@test.org'
                )
                
                # Create book in each database - this should trigger the lock
                book = Book(name=f'Test Book {db}')
                book.save(using=db)
                
                # Force connection usage that can cause locks
                connections[db].cursor().execute('SELECT 1')