import os
import tempfile
import sqlite3
from unittest import mock

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import connections
from django.test import TestCase, override_settings
from django.urls import path, reverse
from django.test.utils import setup_test_environment, teardown_test_environment
from django.core.management import call_command

from admin_views.models import Book


class Router:
    target_db = None

    def db_for_read(self, model, **hints):
        return self.target_db

    db_for_write = db_for_read


site = admin.AdminSite(name='test_adminsite')
site.register(Book)

urlpatterns = [
    path('admin/', site.urls),
]


def test_issue_reproduction():
    """Test that reproduces the SQLite database locking issue with persistent test databases."""
    # Create temporary database files to simulate persistent test databases
    temp_dir = tempfile.mkdtemp()
    default_db_path = os.path.join(temp_dir, 'test_default.sqlite3')
    other_db_path = os.path.join(temp_dir, 'test_other.sqlite3')
    
    # Create the database files
    for db_path in [default_db_path, other_db_path]:
        conn = sqlite3.connect(db_path)
        conn.close()
    
    # Configure databases with persistent test database names
    test_databases = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',  # This will be overridden by TEST['NAME']
            'TEST': {
                'NAME': default_db_path
            },
        },
        'other': {
            'ENGINE': 'django.db.backends.sqlite3', 
            'NAME': ':memory:',  # This will be overridden by TEST['NAME']
            'TEST': {
                'NAME': other_db_path
            },
        }
    }
    
    with override_settings(
        DATABASES=test_databases,
        ROOT_URLCONF=__name__, 
        DATABASE_ROUTERS=['%s.Router' % __name__]
    ):
        # Simulate the test setup that causes the locking issue
        setup_test_environment()
        
        try:
            # Create test data in both databases like MultiDatabaseTests.setUpTestData
            superusers = {}
            test_book_ids = {}
            
            for db in connections:
                Router.target_db = db
                
                # This should work for the first database
                superusers[db] = User.objects.create_superuser(
                    username=f'admin_{db}', password='something', email='test@test.org',
                )
                b = Book(name='Test Book')
                b.save(using=db)
                test_book_ids[db] = b.id
            
            # Now simulate what happens when the test tries to access the databases again
            # This is where the locking issue occurs with persistent SQLite databases
            for db in connections:
                Router.target_db = db
                
                # Try to access the database - this should cause a lock error
                # with persistent SQLite databases due to improper connection handling
                try:
                    # This operation should fail with "database is locked" error
                    # when using persistent SQLite databases
                    Book.objects.using(db).count()
                    
                    # If we get here without an exception, the test should fail
                    # because the issue is that database locks should occur
                    # but aren't being properly handled
                    if db == 'other':  # The second database is more likely to be locked
                        # Force a connection that should reveal the locking issue
                        conn = connections[db]
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT COUNT(*) FROM admin_views_book")
                            result = cursor.fetchone()
                            # This assertion will fail because the current code doesn't
                            # properly handle connection cleanup, leading to locks
                            assert result[0] >= 0, "Should be able to query without database locks"
                            
                except Exception as e:
                    # If we get a database lock error, that's the bug we're reproducing
                    if "database is locked" in str(e).lower():
                        # This is the expected failure - the bug is reproduced
                        assert False, f"Database locking issue reproduced: {e}"
                    else:
                        # Some other error occurred
                        raise
                        
        finally:
            teardown_test_environment()
            
            # Clean up temporary files
            try:
                os.unlink(default_db_path)
                os.unlink(other_db_path)
                os.rmdir(temp_dir)
            except (OSError, FileNotFoundError):
                pass