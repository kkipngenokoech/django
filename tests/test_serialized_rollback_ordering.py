import pytest
from django.test import TransactionTestCase
from django.db import models, connection
from django.apps import apps
from django.core.management import call_command
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader
from django.test.utils import setup_test_environment, teardown_test_environment
from django.conf import settings
from io import StringIO
from django.core import serializers


class Author(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'


class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that deserialize_db_from_string fails due to foreign key ordering constraints."""
    # Setup test environment
    if not settings.configured:
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=['__main__'],
            USE_TZ=False,
        )
    
    # Register models with Django's app registry
    from django.apps.registry import apps
    if not apps.ready:
        apps.populate(settings.INSTALLED_APPS)
    
    # Create tables
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Author)
        schema_editor.create_model(Book)
    
    try:
        # Create test data with foreign key relationship
        author = Author.objects.create(name='Test Author')
        book = Book.objects.create(title='Test Book', author=author)
        
        # Serialize the database state
        creation = connection.creation
        serialized_data = creation.serialize_db_to_string()
        
        # Clear the database
        Book.objects.all().delete()
        Author.objects.all().delete()
        
        # Manually craft serialized data that has Book before Author to trigger the bug
        # This simulates the case where sort_dependencies doesn't handle FK ordering properly
        data = [
            {
                "model": "__main__.book",
                "pk": book.pk,
                "fields": {
                    "title": "Test Book",
                    "author": author.pk
                }
            },
            {
                "model": "__main__.author", 
                "pk": author.pk,
                "fields": {
                    "name": "Test Author"
                }
            }
        ]
        
        import json
        bad_serialized_data = json.dumps(data)
        
        # This should fail because Book references Author but Author comes after Book
        # The current implementation doesn't wrap in a transaction to handle this
        with pytest.raises(Exception):  # Should raise IntegrityError or similar
            creation.deserialize_db_from_string(bad_serialized_data)
            
    finally:
        # Cleanup
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(Book)
            schema_editor.delete_model(Author)