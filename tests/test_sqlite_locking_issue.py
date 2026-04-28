import os
import tempfile
from unittest import mock

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import connections
from django.test import TestCase, override_settings
from django.urls import path, reverse

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
    # Create temporary SQLite files to simulate persistent test databases
    with tempfile.TemporaryDirectory() as temp_dir:
        default_db = os.path.join(temp_dir, 'test_default.sqlite3')
        other_db = os.path.join(temp_dir, 'test_other.sqlite3')
        
        databases_config = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': default_db,
                'TEST': {
                    'NAME': default_db
                },
            },
            'other': {
                'ENGINE': 'django.db.backends.sqlite3', 
                'NAME': other_db,
                'TEST': {
                    'NAME': other_db
                },
            }
        }
        
        with override_settings(
            DATABASES=databases_config,
            ROOT_URLCONF=__name__, 
            DATABASE_ROUTERS=['%s.Router' % __name__]
        ):
            # Simulate the MultiDatabaseTests scenario that causes locking
            test_case = TestCase()
            test_case.databases = {'default', 'other'}
            
            # This will fail with "database is locked" error when using persistent SQLite databases
            # because connections aren't properly closed between database operations
            superusers = {}
            test_book_ids = {}
            
            for db in connections:
                Router.target_db = db
                # Force creation of connection to both databases simultaneously
                connection = connections[db]
                connection.ensure_connection()
                
                # This creates the locking scenario - multiple connections to SQLite files
                superusers[db] = User.objects.create_superuser(
                    username=f'admin_{db}', password='something', email=f'test_{db}@test.org',
                )
                b = Book(name=f'Test Book {db}')
                b.save(using=db)
                test_book_ids[db] = b.id
            
            # The issue manifests when trying to perform operations on both databases
            # without properly managing connections
            for db in connections:
                Router.target_db = db
                # This will trigger the "database is locked" error
                Book.objects.using(db).filter(id=test_book_ids[db]).update(name=f'Updated Book {db}')